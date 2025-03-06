# WAJE LOYALITY API

## Role-based Access Control
- Role-based Access Control: this feature ensures only user's with the right kind of permission can 
perform certain actions. Client requested for Auditor's to only view created Vouchers. A custom permission class, VoucherPermission, was implemented to achieve this. The User model was updated by making the role field a foreign key to the Role model 