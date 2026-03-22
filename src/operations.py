from bson import ObjectId

def serialize_doc(doc):
    return {k: str(v) if isinstance(v, ObjectId) else v for k, v in doc.items()}