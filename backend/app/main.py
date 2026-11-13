# Import the FastAPI class from the fastapi package
from fastapi import FastAPI

# Create an instance of the FastAPI application
# The title appears in the automatically generated interactive documentation (/docs)
app = FastAPI(title="Event Second Brain API")


# Define a GET endpoint at the path "/health"
# This is a simple health-check route used to verify that the server is running properly
@app.get("/health")
def health_check():
    # Return a basic JSON response confirming status
    return {"status": "ok"}
