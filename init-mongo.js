db = db.getSiblingDB('personnel_data'); // Use your database name

// Define the capped collection size in bytes (e.g., 100MB)
const cappedSize = 10 * 1024 * 1024 * 1024; // 10GB

// Create a capped collection if it doesn't exist
if (!db.getCollectionNames().includes('daily_snapshots')) {
    db.createCollection('daily_snapshots', { capped: true, size: cappedSize });
}