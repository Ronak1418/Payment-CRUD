from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from typing import List, Optional
from datetime import date, datetime
from bson import ObjectId
import pandas as pd
import os
from config.db import payment_collection, evidence_collection
from models.model import Payment
from bson import ObjectId
from fastapi import FastAPI,Query, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware

def serialize_document(doc):
    """Convert MongoDB ObjectId to string for JSON serialization."""
    if "_id" in doc:
        doc["_id"] = str(doc["_id"])
    return doc

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# @app.on_event("startup")
# async def startup_event():
#     csv_file_path = "api/payment_information.csv" 
#     await load_csv_to_db(csv_file_path)


def parse_datetime(date_string):
    formats = [
        "%Y-%m-%d",                # For '2024-12-31'
        "%Y-%m-%dT%H:%M:%S.%fZ",   # For '2025-01-12T07:00:00.000Z'
        "%Y-%m-%dT%H:%M:%S",       # For '2025-01-12T07:00:00'
        "%Y-%m-%dT%H:%M:%S.%f",    # For '2025-01-12T07:00:00.123456'
    ]
    
    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue
    
    raise ValueError(f"Date string '{date_string}' does not match any known formats")

def update_payment_status(payment):
  today = datetime.utcnow().date()
  if isinstance(payment['payee_due_date'], str):
    payee_due_date = parse_datetime(payment['payee_due_date']).date()
  else:
    payee_due_date = datetime.utcfromtimestamp(payment['payee_due_date']).date()

  if payee_due_date == today:
    payment['payee_payment_status'] = "due_now"
  elif payee_due_date< today:
    payment['payee_payment_status'] = "overdue"

  return payment

def calculate_total_due(payment):
  discount_amount=(payment.due_amount*payment.discount_percent)/100
  tax_amount = (payment.due_amount*payment.tax_percent)/100
  total_due = payment.due_amount - discount_amount + tax_amount
  return total_due

def calculate_total_due_get(payment):
  discount_amount=(payment['due_amount']*payment['discount_percent'])/100
  tax_amount = (payment['due_amount']*payment['tax_percent'])/100
  total_due = payment['due_amount'] - discount_amount + tax_amount
  print(total_due)
  return total_due

@app.get("/payments")
async def get_payments(

    search: str = Query(None),
    filter_status: str = Query(None),
    page: int = Query(1, ge=1),
    skip: int = 0,
    limit:int = Query(20)
    ):

  query = {}

  skip = (page-1)*limit

  payments = await payment_collection.find(query).sort("payee_added_date_utc", -1).to_list(length=None)

  for payment in payments:
    payment = update_payment_status(payment)
    payment['total_due'] = calculate_total_due_get(payment)
    payment['_id'] = str(payment['_id'])

  if filter_status:
    payments = [payment for payment in payments if payment['payee_payment_status'] == filter_status]

  if search:
    payments = [payment for payment in payments if (
      search.lower() in payment.get('payee_first_name', '').lower() or 
      search.lower() in payment.get('payee_last_name', '').lower()or
      search.lower() in payment.get('payee_email', '').lower())]

  total_payments = len(payments)
  start_index = (page - 1) * limit
  end_index = start_index + limit

    # Ensure slicing doesn't go out of bounds
  paginated_payments = payments[start_index:end_index]
  return paginated_payments

@app.post("/create_payment")
async def create_payment(payment: Payment):
    payment_dict = payment.dict()
    payment_dict["total_due"] = calculate_total_due(payment)
    result = await payment_collection.insert_one(payment_dict)
    return {"id": str(result.inserted_id)}

@app.put("/update_payment/{id}")
async def update_payment(id: str, payment: Payment):
    payment_dict = payment.dict()
    payment_dict["total_due"] = calculate_total_due(payment)
    print(id)
    updated = await payment_collection.update_one(
        {"_id": ObjectId(id)}, {"$set": payment_dict}
    )

    if updated.modified_count == 1:
        return {"message": "Payment updated successfully."}
    raise HTTPException(status_code=404, detail="Payment not found.")

@app.delete("/delete_payment/{payment_id}")
async def delete_payment(payment_id: str):
    deleted = await payment_collection.delete_one({"_id": ObjectId(payment_id)})
    if deleted.deleted_count == 1:
        return {"message": "Payment deleted successfully."}
    raise HTTPException(status_code=404, detail="Payment not found.")

# @app.post("/upload_evidence/{payment_id}")
# async def upload_evidence(payment_id: str, file: UploadFile = File(...)):
#     if file.content_type not in ["application/pdf", "image/png", "image/jpeg"]:
#         raise HTTPException(status_code=400, detail="Invalid file type. Only PDF, PNG, and JPG are allowed.")

#     file_path = f"evidence_{payment_id}_{file.filename}"
#     with open(file_path, "wb") as f:
#         f.write(file.file.read())

#     evidence_collection.update_one(
#         {"payment_id": ObjectId(payment_id)},
#         {"$set": {"file_path": file_path, "content_type": file.content_type}},
#         upsert=True,
#     )

#     await payment_collection.update_one(
#         {"_id": ObjectId(payment_id)}, {"$set": {"payee_payment_status": "completed"}}
#     )
#     return {"message": "Evidence file uploaded successfully."}

# @app.get("/download_evidence/{payment_id}")
# async def download_evidence(payment_id: str):
#     evidence = await evidence_collection.find_one({"payment_id": ObjectId(payment_id)})
#     if not evidence:
#         raise HTTPException(status_code=404, detail="Evidence not found.")

#     return FileResponse(evidence["file_path"], media_type=evidence["content_type"], filename=os.path.basename(evidence["file_path"]))
