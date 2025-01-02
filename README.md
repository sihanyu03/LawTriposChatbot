# RAGChatbot

Deployment process:
- Create AWS account, copy AWS API key to .aws/credentials
- Create Dockerfile, requirements.txt
- Create ECR repository, 
- Push image to ECR (AWS has all the commands)
- Build image using AWS provided command
- Create Lambda function, with the above created image
- Create function URL (select NONE as Auth type), Function URL is backend url	
- No need to configure CORS in AWS, it's done in the backend
- Logs can be seen from the Monitor tab