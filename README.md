# WAJE LOYALITY API

version = 2.0.0

## Role-based Access Control
- Role-based Access Control: this feature ensures only user's with the right kind of permission can 
perform certain actions. 
- Client requested for Auditor's to only view created Vouchers. A custom permission classes, IsAdmin, IsAuditor, IsAccountant, were implemented to achieve this. 
- The User model was updated by making the role field a foreign key to the Role model 

## Technical API Documentation
- Replaced drf-yasg with drf-spectacular which is more modern and based on openAPI 3
- The drf-yasg was not correctly interpreting the api endpoints
- To make further changes to the existing basic configuration, refer to `https://drf-spectacular.readthedocs.io/en/latest/readme.html`
- To generate schema, run the command below.
```
    python manage.py spectacular --color --file schema.yml
```