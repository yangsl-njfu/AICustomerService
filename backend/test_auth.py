from services.auth_service import AuthService

auth = AuthService()
hashed = auth.hash_password('123456')
print(f'Hashed: {hashed}')
print(f'Verify: {auth.verify_password("123456", hashed)}')
