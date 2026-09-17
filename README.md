
  # Generate a migration by comparing models to database                                                                                                                                   
  uv run alembic revision --autogenerate -m "description"                                                                                                                                  
                                              
  # Apply all pending migrations                                                                                                                                                           
  uv run alembic upgrade head                                                                                                                                                              
                                                                                                                                                                                           
  # Roll back the last migration                                                                                                                                                           
  uv run alembic downgrade -1                                                                                                                                                              
                                                                                                                                                                                           
  # Show current migration state                                                                                                                                                           
  uv run alembic current                                                                                                                                                                   
                                                                                                                                                                                           
  # Show migration history                                                                                                                                                                 
  uv run alembic history    