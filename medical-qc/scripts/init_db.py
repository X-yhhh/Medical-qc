import asyncio
import sys
import os

# Add the project root to the python path
sys.path.append(os.getcwd())

from app.utils.database import AsyncSessionLocal
from app.models.user_role import UserRole
from app.models.user import User
from app.models.hemorrhage_record import HemorrhageRecord
from sqlalchemy import select

async def init_db():
    async with AsyncSessionLocal() as session:
        print("Checking roles...")
        result = await session.execute(select(UserRole))
        roles = result.scalars().all()
        
        role_names = {r.name for r in roles}
        print(f"Existing roles: {role_names}")
        
        roles_to_add = []
        if "admin" not in role_names:
            roles_to_add.append(UserRole(id=1, name="admin", description="Administrator"))
        if "doctor" not in role_names:
            roles_to_add.append(UserRole(id=2, name="doctor", description="Doctor"))
            
        if roles_to_add:
            print(f"Adding roles: {[r.name for r in roles_to_add]}")
            session.add_all(roles_to_add)
            await session.commit()
            print("Roles added successfully.")
        else:
            print("All necessary roles exist.")

if __name__ == "__main__":
    asyncio.run(init_db())
