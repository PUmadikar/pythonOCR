cmd command to zip file

powershell Compress-Archive -Path OCR\\lambda_function.py -DestinationPath lambda_function.zip



? Overview
This Lambda function is triggered by an S3 event (when a PDF file is uploaded to an S3 bucket). It uses Amazon Textract to extract text from the PDF and saves the output as a .txt file in a different S3 bucket.

?? Step-by-Step Breakdown
1. Get S3 Event Data

bucket_name = event['Records'][0]['s3']['bucket']['name']
file_name = event['Records'][0]['s3']['object']['key']
o Extracts the source bucket name and file name (PDF) from the S3 event.

2. Initialize Clients

textract = boto3.client('textract')
s3 = boto3.client('s3')
o Initializes the boto3 clients for Textract and S3.

3. Start Textract Job
\
response = textract.start_document_text_detection(...)
job_id = response['JobId']
o Starts an asynchronous Textract job to detect text in the PDF.
o Returns a job ID to track the job status.

4. Polling for Job Completion

while True:
    result = textract.get_document_text_detection(JobId=job_id)
    ...
    time.sleep(2)
o Periodically checks job status until it is either SUCCEEDED or FAILED.

5. Extract Text if Job Succeeds

for item in result['Blocks']:
    if item['BlockType'] == 'LINE':
        detected_text.append(item['Text'])
o If successful, paginates through Textract results and extracts line-level text blocks.

6. Save to S3 Output Bucket

s3.put_object(
    Bucket=output_bucket,
    Key=output_key,
    Body=full_text.encode('utf-8')
)
o Joins all detected text and saves it as a .txt file in a predefined output bucket.

7. Return Response
o Returns a 200 status and the extracted text + output file location if successful.
o Returns a 500 error if the Textract job failed.


* Event-driven architecture using S3 + Lambda.
* Asynchronous processing with start_document_text_detection.
* Polling using get_document_text_detection.
* Handling pagination via NextToken.
* Storing results back in S3.

?? Optional Enhancements (mention if asked):
* Replace polling with Step Functions for better scalability.
* Add error handling or retries.
* Use SNS or EventBridge for job completion notification.

