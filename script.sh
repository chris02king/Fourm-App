docker build -t trip-feedback-app .
docker run -d -p 443:5002 trip-feedback-app