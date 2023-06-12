# YouTubeTranscriptAPI Imports
from youtube_transcript_api import YouTubeTranscriptApi, NoTranscriptFound, VideoUnavailable, TooManyRequests, \
    TranscriptsDisabled, NoTranscriptAvailable
from youtube_transcript_api.formatters import TextFormatter

# Flask Imports
from flask import Flask, jsonify, request, send_from_directory, render_template, redirect

# NLTK Imports
import nltk

# Other Imports
import os
import sys

# Summarizer Import (Our Another File: summarizer.py)
from summarizer import gensim_summarize, spacy_summarize, nltk_summarize, sumy_lsa_summarize, sumy_luhn_summarize, \
    sumy_text_rank_summarize

# Waitress Import for Serving at Heroku
#from waitress import serve

app = Flask(__name__)

@app.route('/summarize/', methods=['GET'])
def transcript_fetched_query():
    # Getting argument from the request
    video_id = request.args.get('id')  # video_id of the YouTube Video
    percent = request.args.get('percent')  # percentage of the summary
    choice = request.args.get('choice')  # summarization choice

    # Checking whether all parameters exist or not
    if video_id and percent and choice:
        # Every parameter exists here: checking validity of choice
        choice_list = ["gensim-sum", "spacy-sum", "nltk-sum", "sumy-lsa-sum", "sumy-luhn-sum", "sumy-text-rank-sum"]
        if choice in choice_list:
            # Choice Correct: Proceeding with Transcript Fetch and its Summarization
            try:
                # Using Formatter to store and format received subtitles properly.
                formatter = TextFormatter()
                transcript = YouTubeTranscriptApi.get_transcript(video_id)
                # transcript_list = YouTubeTranscriptApi.list_transcripts('video_id')
                # transcript = transcript_list.find_manually_created_transcript(['de', 'en'])
                # transcript = transcript_list.find_generated_transcript(['de', 'en'])
                formatted_text = formatter.format_transcript(transcript).replace("\n", " ")

                # Checking the length of sentences in formatted_text string, before summarizing it.
                num_sent_text = len(nltk.sent_tokenize(formatted_text))
                # num_sent_text = len(nltk.sent_tokenize(transcript))

                # Pre-check if the summary will have at least one line .
                select_length = int(num_sent_text * (int(percent) / 100))

                # Summary will have at least 1 line. Proceed to summarize.
                if select_length > 0:

                    # Condition satisfied for summarization, summarizing the formatted_text based on choice.
                    if num_sent_text > 1:

                        # Summarizing Formatted Text based upon the request's choice
                        if choice == "gensim-sum":
                            summary = gensim_summarize(formatted_text, percent)  # Gensim Library for TextRank Based Summary.
                            # summary  = gensim_summarize(transcript, percent)
                        elif choice == "spacy-sum":
                            summary = spacy_summarize(formatted_text,
                                                      percent)  # Spacy Library for frequency-based summary.
                        elif choice == "nltk-sum":
                            summary = nltk_summarize(formatted_text,
                                                     percent)  # NLTK Library used for frequency-based summary.
                        elif choice == "sumy-lsa-sum":
                            summary = sumy_lsa_summarize(formatted_text,
                                                         percent)  # Sumy for extractive summary using LSA.
                        elif choice == "sumy-luhn-sum":
                            summary = sumy_luhn_summarize(formatted_text,
                                                          percent)  # Sumy Library for TF-IDF Based Summary.
                        elif choice == "sumy-text-rank-sum":
                            summary = sumy_text_rank_summarize(formatted_text,
                                                               percent)  # Sumy for Text Rank Based Summary.
                        else:
                            summary = None

                        # Checking the length of sentences in summary string.
                        num_sent_summary = len(nltk.sent_tokenize(summary))

                        # Returning Result
                        response_list = {
                            # 'fetched_transcript': formatted_text,
                            'processed_summary': summary,
                            'length_original': len(formatted_text),
                            'length_summary': len(summary),
                            'sentence_original': num_sent_text,
                            'sentence_summary': num_sent_summary
                        }

                        return jsonify(success=True,
                                       message="Subtitles for this video was fetched and summarized successfully.",
                                       response=response_list), 200

                    else:
                        return jsonify(success=False,
                                       message="Subtitles are not formatted properly for this video. Unable to "
                                               "summarize. There is a possibility that there is no punctuation in "
                                               "subtitles of your video.",
                                       response=None), 400

                else:
                    return jsonify(success=False,
                                   message="Number of lines in the subtitles of your video is not "
                                           "enough to generate a summary. Number of sentences in your video: {}"
                                   .format(num_sent_text),
                                   response=None), 400

            # Catching Exceptions
            except VideoUnavailable:
                return jsonify(success=False, message="VideoUnavailable: The video is no longer available.",
                               response=None), 400
            except TooManyRequests:
                return jsonify(success=False,
                               message="TooManyRequests: YouTube is receiving too many requests from this IP."
                                       " Wait until the ban on server has been lifted.",
                               response=None), 500
            except TranscriptsDisabled:
                return jsonify(success=False, message="TranscriptsDisabled: Subtitles are disabled for this video.",
                               response=None), 400
            except NoTranscriptAvailable:
                return jsonify(success=False,
                               message="NoTranscriptAvailable: No transcripts are available for this video.",
                               response=None), 400
            except NoTranscriptFound:
                return jsonify(success=False, message="NoTranscriptAvailable: No transcripts were found.",
                               response=None), 400
            except Exception as e:
                # Prevent server error by returning this message to all other un-expected errors.
                print(e)
                sys.stdout.flush()
                return jsonify(success=False,
                               message="Some error occurred."
                                       " Contact the administrator if it is happening too frequently.",
                               response=None), 500
        else:
            return jsonify(success=False,
                           message="Invalid Choice: Please create your request with correct choice.",
                           response=None), 400
    elif video_id is None or len(video_id) <= 0:
        # video_id parameter doesn't exist in the request.
        return jsonify(success=False,
                       message="Video ID is not present in the request. "
                               "Please check that you have added id in your request correctly.",
                       response=None), 400
    elif percent is None or len(percent) <= 0:
        # percent parameter doesn't exist.
        return jsonify(success=False,
                       message="No Percentage value is present in the request. "
                               "Please check whether your request is correct.",
                       response=None), 400
    elif choice is None or len(choice) <= 0:
        # choice parameter for the summary type doesn't exist here.
        return jsonify(success=False,
                       message="No Choice parameter is present in the request. "
                               "Please request along with your choice correctly.",
                       response=None), 400
    else:
        # Some another edge case happened. Return this message for preventing exception throw.
        return jsonify(success=False,
                       message="Please request the server with your arguments correctly.",
                       response=None), 400




@app.route('/text_summarize/', methods=['GET'])
def text_summary():
    text = request.args.get('text_input')
    percent = request.args.get('percent')  # percentage of the summary
    choice = request.args.get('choice')  # summarization choice

    if text and percent and choice:
        choice_list = ["gensim-sum", "spacy-sum", "nltk-sum", "sumy-lsa-sum", "sumy-luhn-sum", "sumy-text-rank-sum"]
        if choice in choice_list:
            # Choice Correct: Proceeding with Transcript Fetch and its Summarization
            try:
                select_length = int(len(text) * (int(percent) / 100))

                # Summary will have at least 1 line. Proceed to summarize.
                if select_length > 0:

                    # Condition satisfied for summarization, summarizing the formatted_text based on choice.
                    if len(text) > 1:

                        # Summarizing Formatted Text based upon the request's choice
                        if choice == "gensim-sum":
                            summary = gensim_summarize(text,
                                                       percent)  # Gensim Library for TextRank Based Summary.
                        elif choice == "spacy-sum":
                            summary = spacy_summarize(text,
                                                      percent)  # Spacy Library for frequency-based summary.
                        elif choice == "nltk-sum":
                            summary = nltk_summarize(text,
                                                     percent)  # NLTK Library used for frequency-based summary.
                        elif choice == "sumy-lsa-sum":
                            summary = sumy_lsa_summarize(text,
                                                         percent)  # Sumy for extractive summary using LSA.
                        elif choice == "sumy-luhn-sum":
                            summary = sumy_luhn_summarize(text,
                                                          percent)  # Sumy Library for TF-IDF Based Summary.
                        elif choice == "sumy-text-rank-sum":
                            summary = sumy_text_rank_summarize(text,
                                                               percent)  # Sumy for Text Rank Based Summary.
                        else:
                            summary = None

                        # Checking the length of sentences in summary string.
                        num_sent_summary = len(nltk.sent_tokenize(summary))

                        # Returning Result
                        response_list = {
                            # 'fetched_transcript': formatted_text,
                            'processed_summary': summary,
                            'length_summary': len(summary),
                            'sentence_original': len(text),
                            'sentence_summary': num_sent_summary
                        }

                        return jsonify(success=True,
                                       message="Text was fetched and summarized successfully.",
                                       response=response_list), 200
                    else:
                        return jsonify(success=False,
                                       message="Unable to summarize. There is a possibility that there is no punctuation in text.",
                                       response=None), 400

                else:
                    return jsonify(success=False,
                                   message="Number of lines in the  text is not "
                                           "enough to generate a summary. Number of sentences in your text: {}"
                                   .format(len(text)),
                                   response=None), 400

        
            except Exception as e:
                # Prevent server error by returning this message to all other un-expected errors.
                print(e)
                sys.stdout.flush()
                return jsonify(success=False,
                               message="Some error occurred."
                                       " Contact the administrator if it is happening too frequently.",
                               response=None), 500
        else:
            return jsonify(success=False,
                           message="Invalid Choice: Please create your request with correct choice.",
                           response=None), 400
    elif text is None or len(text) <= 0:
        # video_id parameter doesn't exist in the request.
        return jsonify(success=False,
                       message="Text is not present in the request.",
                       response=None), 400
    elif percent is None or len(percent) <= 0:
        # percent parameter doesn't exist.
        return jsonify(success=False,
                       message="No Percentage value is present in the request. "
                               "Please check whether your request is correct.",
                       response=None), 400
    elif choice is None or len(choice) <= 0:
        # choice parameter for the summary type doesn't exist here.
        return jsonify(success=False,
                       message="No Choice parameter is present in the request. "
                               "Please request along with your choice correctly.",
                       response=None), 400
    else:
        # Some another edge case happened. Return this message for preventing exception throw.
        return jsonify(success=False,
                       message="Please request the server with your arguments correctly.",
                       response=None), 400
        



@app.route('/favicon.ico')
# Favicon is stored in static folder, browsers request it to display along with tab title.
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'), 'favicon.png',
                               mimetype='image/vnd.microsoft.icon')



@app.route('/')
def summarizer_web():
    # We are at web.html, online input boxes are there to summarize the given video URL.
    # Displaying web.html to the end user
    return render_template('web2.html')



if __name__ == '__main__':
    # Running Flask Application
    app.run()
    #flask_app = create_app()
    #serve(flask_app, host='0.0.0.0', port=80, debug=True, url_scheme='https')
    #serve(flask_app, host='0.0.0.0', port=80, url_scheme='https')




