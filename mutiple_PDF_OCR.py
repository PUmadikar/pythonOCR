import json
import boto3
import time

def handler(event, context):
    textract = boto3.client('textract')
    s3 = boto3.client('s3')
    output_bucket = 'textract-ocr-output-bucket'

    results = []

    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        print('bucket_name - ',bucket_name)
        file_name = record['s3']['object']['key']
        print('file_name - ',file_name)

        print(f"Processing file: s3://{bucket_name}/{file_name}")

        # Start Textract job
        response = textract.start_document_text_detection(
            DocumentLocation={
                'S3Object': {
                    'Bucket': bucket_name,
                    'Name': file_name
                }
            }
        )

        job_id = response['JobId']
        print(f"Started job with ID: {job_id} for file: {file_name}")

        # Wait for job to complete
        while True:
            result = textract.get_document_text_detection(JobId=job_id)
            status = result['JobStatus']
            if status in ['SUCCEEDED', 'FAILED']:
                break
            print(f"Waiting for job {job_id} to complete...")
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
            print(f"Extracted text for {file_name}:\n{full_text}")

            # Save to output bucket
            output_key = file_name.replace('.pdf', '.txt')
            s3.put_object(
                Bucket=output_bucket,
                Key=output_key,
                Body=full_text.encode('utf-8')
            )

            results.append({
                'file': file_name,
                'output_file': f's3://{output_bucket}/{output_key}',
                'status': 'SUCCEEDED'
            })

        else:
            print(f"Textract job failed for {file_name}")
            results.append({
                'file': file_name,
                'status': 'FAILED'
            })

    return {
        'statusCode': 200,
        'body': json.dumps(results)
    }
