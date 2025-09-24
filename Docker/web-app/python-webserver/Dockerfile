FROM rockylinux:9

# Install Python 3.9 and other necessary packages
 RUN dnf install -y python39 && dnf clean all
#
# # Set the working directory
 WORKDIR /app
#
# # Copy the application code
 COPY server.py .
#
# # Expose the port the app runs on
 EXPOSE 8080
#
# # Run the Python server
 CMD ["python3", "server.py"]

