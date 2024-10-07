docker build -t trip-feedback-app .
docker run -d -p 80:5002 trip-feedback-app