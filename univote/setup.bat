# Copy .env.example to .env first, then run this script
# Run from the univote/ directory

# Step 1: Create & activate venv
python -m venv venv
venv\Scripts\activate

# Step 2: Install dependencies
pip install -r requirements.txt

# Step 3: Copy env file
copy .env.example .env
echo "EDIT .env with your DB password before continuing!"

# Step 4: Run migrations
python manage.py makemigrations accounts
python manage.py makemigrations students
python manage.py makemigrations elections
python manage.py makemigrations voting
python manage.py makemigrations audit
python manage.py migrate

# Step 5: Create cache table
python manage.py createcachetable

# Step 6: Collect static files
python manage.py collectstatic --noinput

# Step 7: Load seed data
python seed/seed_data.py

# Step 8: Run server
python manage.py runserver
