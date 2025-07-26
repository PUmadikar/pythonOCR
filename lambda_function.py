import json
import boto3
import time

def handler(event, context):
    # Get bucket and file name from event
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    print('bucket_name-',bucket_name)
    file_name = event['Records'][0]['s3']['object']['key']
    print('file_name -',file_name)

    textract = boto3.client('textract')
    s3 = boto3.client('s3')
    output_bucket = 'textract-ocr-output-bucket'

    # Start asynchronous job for PDF document
    response = textract.start_document_text_detection(
        DocumentLocation={



            'S3Object': {
                'Bucket': bucket_name,
                'Name': file_name
            }
        }
    )

    job_id = response['JobId']
    print(f"Started job with ID: {job_id}")

    # Wait for job to complete
    while True:
        result = textract.get_document_text_detection(JobId=job_id)
        status = result['JobStatus']
        if status in ['SUCCEEDED', 'FAILED']:
            break
        print("Waiting for job to complete...")
        time.sleep(2)

    if status == 'SUCCEEDED':
        detected_text = []
        next_token = None

        while True:
            if next_token:
                result = textract.get_document_text_detection(JobId=job_id, NextToken=next_token)
            else:
                result = textract.get_document_text_detection(JobId=job_id)

            for item in result['Blocks']:
                if item['BlockType'] == 'LINE':
                    detected_text.append(item['Text'])

            next_token = result.get('NextToken')
            if not next_token:
                break

        full_text = "\n".join(detected_text)
        print(full_text)


        # Save extracted text to output S3 bucket
        output_key = file_name.replace('.pdf', '.txt')
        s3.put_object(
            Bucket=output_bucket,
            Key=output_key,
            Body=full_text.encode('utf-8')
        )

        return {
            'statusCode': 200,
            'body': json.dumps({
                'extracted_text': detected_text,
                'output_file': f's3://{output_bucket}/{output_key}'
            })
        }
    else:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Textract job failed'})
        }
