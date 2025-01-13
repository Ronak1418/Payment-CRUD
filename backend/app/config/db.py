from motor.motor_asyncio import AsyncIOMotorClient
MONGO_DETAILS = "mongodb+srv://patelronakkumar1418:ExZpPHwn1RgCgdht@cluster0.m44c8.mongodb.net/"
client = AsyncIOMotorClient(MONGO_DETAILS)
database = client.paymentDB
payment_collection = database.get_collection("payments")
evidence_collection = database.get_collection("evidence")