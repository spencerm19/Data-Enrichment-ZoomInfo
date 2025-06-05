from fastapi import FastAPI, UploadFile, File, HTTPException
from enrichment import enrich_data, EnrichmentError
import os
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = FastAPI()

@app.get("/health")
def health_check():
    """Health check endpoint"""
    logging.info("Health check requested")
    return {"status": "healthy"}

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """
    Upload and process a CSV file
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Only CSV files are allowed")
    
    # Create uploads directory if it doesn't exist
    os.makedirs("uploads", exist_ok=True)
    
    # Save the uploaded file
    file_location = f"uploads/{file.filename}"
    try:
        with open(file_location, "wb+") as file_object:
            file_object.write(await file.read())
    except Exception as e:
        logging.error(f"Error saving file: {str(e)}")
        raise HTTPException(status_code=500, detail="Could not save the file")
    
    # Process the file
    try:
        result = enrich_data(file_location)
        return {"result": result}
    except EnrichmentError as e:
        logging.error(f"Error processing file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        # Clean up the uploaded file
        if os.path.exists(file_location):
            os.remove(file_location) 