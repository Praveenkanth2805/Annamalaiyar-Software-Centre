import bcrypt

# original password
password = "admin123"

# convert to bytes
password_bytes = password.encode('utf-8')

# generate salt & hash
hashed_password = bcrypt.hashpw(password_bytes, bcrypt.gensalt())

print(hashed_password)
