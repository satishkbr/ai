import json
import boto3
import time
import urllib


# Initialize Boto3 clients for Transcribe and S3
transcribe_client = boto3.client('transcribe')
translate = boto3.client('translate')
polly = boto3.client('polly')
s3 = boto3.client('s3')
def lambda_handler(event, context):
    # Extract the audio file URL or base64-encoded audio data from the event
    def transcribe_file(job_name, file_uri, transcribe_client):
        transcribe_client.start_transcription_job(
            TranscriptionJobName=job_name,
            Media={'MediaFileUri': file_uri},
            MediaFormat='mp3',
            LanguageCode='en-US'
        )

        max_tries = 60
        while max_tries > 0:
            max_tries -= 1
            job = transcribe_client.get_transcription_job(TranscriptionJobName=job_name)
            job_status = job['TranscriptionJob']['TranscriptionJobStatus']
            if job_status in ['COMPLETED', 'FAILED']:
                print(f"Job {job_name} is {job_status}.")
                if job_status == 'COMPLETED':
                    response = urllib.request.urlopen(job['TranscriptionJob']['Transcript']['TranscriptFileUri'])
                    data = json.loads(response.read())
                    text = data['results']['transcripts'][0]['transcript']
                    print("========== below is output of speech-to-text ========================")
                    print(text)
                    print("=====================================================================")
                    #translate job
                    translated_text = translate.translate_text(Text=text, SourceLanguageCode="auto", TargetLanguageCode="hi")['TranslatedText']
                    print(f"HIndi translated  is {translated_text}.")
                    
                    #polly task
                    # 5️⃣ Convert text to speech using AWS Polly
                    response = polly.synthesize_speech(
                        Text=translated_text, OutputFormat="mp3", VoiceId="Lucia"
                    )

                    # 6️⃣ Save translated speech to S3
                    s3.put_object(
                        Bucket="my-audio-bucket-satish",
                        Key="translated_file.mp3",
                        Body=response['AudioStream'].read()
                    )
                break
            else:
                print(f"Waiting for {job_name}. Current status is {job_status}.")
            time.sleep(10)
    file_uri = 's3://my-audio-bucket-satish/Recording.mp3'
    transcription_job_name = f"transcription-{int(time.time())}"
    transcribe_file(transcription_job_name, file_uri, transcribe_client)
