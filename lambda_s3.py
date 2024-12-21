import boto3
from PIL import Image
import io

# Initialize S3 client
s3 = boto3.client('s3')

def lambda_handler(event, context):
    source_bucket = event['Records'][0]['s3']['bucket']['ecs-test-s3']
    object_key = event['Records'][0]['s3']['object']['key']
    destination_bucket = "destination-bucket"
    thumbnail_key = f"thumbnails/{object_key}"

    # Supported image extensions
    image_extensions = ('.jpg', '.jpeg', '.png', '.bmp', '.gif', '.tiff')
    
    # Check if the file has an image extension
    if not object_key.lower().endswith(image_extensions):
        print(f"File {object_key} is not an image. Skipping...")
        return {
            'statusCode': 400,
            'body': f"File {object_key} is not an image. No processing done."
        }

    try:
        # Download the object from S3
        response = s3.get_object(Bucket=source_bucket, Key=object_key)
        
        # Check Content-Type to confirm it's an image
        content_type = response['ContentType']
        if not content_type.startswith("image/"):
            print(f"File {object_key} has Content-Type {content_type}, not an image. Skipping...")
            return {
                'statusCode': 400,
                'body': f"File {object_key} is not an image based on Content-Type. No processing done."
            }

        # Process the image
        image_data = response['Body'].read()
        with Image.open(io.BytesIO(image_data)) as image:
            image.thumbnail((128, 128))
            
            # Save thumbnail to a BytesIO stream
            thumbnail_stream = io.BytesIO()
            image.save(thumbnail_stream, format=image.format)
            thumbnail_stream.seek(0)
        
        # Upload the thumbnail back to the destination bucket
        s3.put_object(
            Bucket=destination_bucket,
            Key=thumbnail_key,
            Body=thumbnail_stream,
            ContentType=content_type
        )

        return {
            'statusCode': 200,
            'body': f"Thumbnail created and uploaded to {destination_bucket}/{thumbnail_key}"
        }

    except Exception as e:
        print(f"Error processing file {object_key} from bucket {source_bucket}: {e}")
        raise e
