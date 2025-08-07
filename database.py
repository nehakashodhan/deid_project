from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError  # Updated from ConnectionError
import os
from dotenv import load_dotenv

# Load environment variables from .env file (for security)
load_dotenv()

# MongoDB connection setup
def get_database():
    try:
        # Get connection string from environment variables or use hardcoded (for testing)
        MONGODB_URI = os.getenv("MONGODB_URI", "mongodb+srv://kashodhanneha:Y9cmAlap70dkQ6@cluster0.mongodb.net/?retryWrites=true&w=majority")
        
        # Connect to MongoDB
        client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)  # 5-second timeout
        
        # Test the connection
        client.admin.command('ping')
        print("Connected to MongoDB successfully!")
        
        # Select database and collection
        db = client["deid_database"]  # Database name
        collection = db["users"]      # Collection name for user data
        
        return collection
    
    except ServerSelectionTimeoutError as e:
        print(f"Failed to connect to MongoDB: {e}. Check your internet or MongoDB Atlas IP whitelist.")
        return None
    except Exception as e:
        print(f"An error occurred: {e}")
        return None

# Function to create a new user (Create operation)
def create_user(name, dob, allergies, emergency_contact):
    collection = get_database()
    if collection:
        user_data = {
            "name": name,
            "dob": dob,
            "allergies": allergies.split(",") if allergies else [],  # Convert to list if comma-separated
            "emergency_contact": emergency_contact
        }
        result = collection.insert_one(user_data)
        return str(result.inserted_id)  # Return the MongoDB _id as a string
    return None

# Function to read a user by ID (Read operation)
def get_user(user_id):
    collection = get_database()
    if collection:
        # Convert user_id to ObjectId if needed (assuming string input for now)
        user = collection.find_one({"_id": user_id})
        return user
    return None

# Function to update a user's data (Update operation)
def update_user(user_id, name=None, dob=None, allergies=None, emergency_contact=None):
    collection = get_database()
    if collection:
        update_data = {}
        if name:
            update_data["name"] = name
        if dob:
            update_data["dob"] = dob
        if allergies:
            update_data["allergies"] = allergies.split(",") if allergies else []
        if emergency_contact:
            update_data["emergency_contact"] = emergency_contact
        
        if update_data:
            result = collection.update_one({"_id": user_id}, {"$set": update_data})
            return result.modified_count > 0
    return False

# Function to delete a user (Delete operation)
def delete_user(user_id):
    collection = get_database()
    if collection:
        result = collection.delete_one({"_id": user_id})
        return result.deleted_count > 0
    return False

# Example usage (uncomment to test)
if __name__ == "__main__":
    # Test create user
    user_id = create_user("Rahul Sharma", "1995-06-15", "Peanut Allergy, Pollen Allergy", "Anita Sharma, +91-9876543210")
    print(f"Created user with ID: {user_id}")
    
    # Test read user
    if user_id:
        user = get_user(user_id)
        print("User data:", user)
    
    # Test update user
    if user_id:
        update_user(user_id, emergency_contact="New Contact, +91-1234567890")
        updated_user = get_user(user_id)
        print("Updated user data:", updated_user)
    
    # Test delete user
    if user_id:
        delete_user(user_id)
        print("User deleted")