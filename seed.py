"""
seed.py - Database Seeder
--------------------------
Populates the database with realistic sample data for testing and demonstration.

Creates:
    - 1 admin user
    - 4 regular users
    - 12 IT assets across different types
    - 10 helpdesk tickets in various states
    - Sample comments on tickets

Usage:
    flask seed-db
    or
    python seed.py
"""

from datetime import date, datetime, timedelta
from app import create_app
from app.models import db, User, Asset, Ticket, Comment, AuditLog, RentalItem, Rental


def seed_database():
    """Drop all tables and repopulate with fresh sample data."""
    app = create_app('development')

    with app.app_context():
        print('🌱 Dropping existing tables...')
        db.drop_all()
        print('🌱 Creating tables...')
        db.create_all()

        # ── Users ────────────────────────────────────────────────────── #
        print('👤 Creating users...')

        admin = User(
            username='admin',
            email='admin@secureit.local',
            full_name='Sarah Mitchell',
            department='IT Operations',
            phone='+44 7700 900001',
            role='admin',
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=365),
            last_login=datetime.utcnow() - timedelta(hours=2),
        )
        admin.set_password('Admin@12345')

        alice = User(
            username='alice.jones',
            email='alice.jones@secureit.local',
            full_name='Alice Jones',
            department='Finance',
            phone='+44 7700 900002',
            role='user',
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=200),
            last_login=datetime.utcnow() - timedelta(days=1),
        )
        alice.set_password('Alice@12345')

        bob = User(
            username='bob.smith',
            email='bob.smith@secureit.local',
            full_name='Bob Smith',
            department='Engineering',
            phone='+44 7700 900003',
            role='user',
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=180),
            last_login=datetime.utcnow() - timedelta(days=3),
        )
        bob.set_password('Bob@123456')

        carol = User(
            username='carol.white',
            email='carol.white@secureit.local',
            full_name='Carol White',
            department='HR',
            role='user',
            is_active=True,
            created_at=datetime.utcnow() - timedelta(days=120),
        )
        carol.set_password('Carol@1234')

        dave = User(
            username='dave.brown',
            email='dave.brown@secureit.local',
            full_name='Dave Brown',
            department='Marketing',
            role='user',
            is_active=False,  # Deactivated account - demonstrates A07 defence
            created_at=datetime.utcnow() - timedelta(days=90),
        )
        dave.set_password('Dave@12345')

        db.session.add_all([admin, alice, bob, carol, dave])
        db.session.flush()

        # ── Assets ───────────────────────────────────────────────────── #
        print('📦 Creating assets...')

        assets_data = [
            dict(name='Dell XPS 15 Laptop', asset_tag='LT-001', asset_type='Laptop',
                 manufacturer='Dell', model='XPS 15 9530', serial_number='SN-DELL-001',
                 status='In Use', location='London HQ - Floor 2',
                 purchase_date=date(2023, 3, 15), purchase_cost=1299.99,
                 warranty_expiry=date(2026, 3, 15), assigned_to_id=alice.id,
                 notes='Primary laptop for Finance team lead.'),

            dict(name='MacBook Pro 14"', asset_tag='LT-002', asset_type='Laptop',
                 manufacturer='Apple', model='MacBook Pro M3', serial_number='SN-APPLE-002',
                 status='In Use', location='London HQ - Floor 3',
                 purchase_date=date(2023, 11, 1), purchase_cost=1999.00,
                 warranty_expiry=date(2026, 11, 1), assigned_to_id=bob.id),

            dict(name='HP ProDesk Desktop', asset_tag='DT-001', asset_type='Desktop',
                 manufacturer='HP', model='ProDesk 400 G9', serial_number='SN-HP-003',
                 status='Available', location='IT Storage Room',
                 purchase_date=date(2022, 6, 10), purchase_cost=699.00,
                 warranty_expiry=date(2025, 6, 10)),

            dict(name='Dell PowerEdge R740 Server', asset_tag='SRV-001', asset_type='Server',
                 manufacturer='Dell', model='PowerEdge R740',
                 serial_number='SN-DELLSRV-001',
                 status='In Use', location='Server Room - Rack A1',
                 purchase_date=date(2021, 1, 20), purchase_cost=8500.00,
                 warranty_expiry=date(2026, 1, 20),
                 notes='Primary application server. Do not power off without change approval.'),

            dict(name='Cisco Catalyst 2960 Switch', asset_tag='NET-001', asset_type='Switch',
                 manufacturer='Cisco', model='Catalyst 2960-X',
                 serial_number='SN-CISCO-001',
                 status='In Use', location='Server Room - Rack B2',
                 purchase_date=date(2020, 8, 5), purchase_cost=2200.00,
                 warranty_expiry=date(2025, 8, 5)),

            dict(name='Dell UltraSharp 27" Monitor', asset_tag='MON-001', asset_type='Monitor',
                 manufacturer='Dell', model='U2722D',
                 serial_number='SN-DELLMON-001',
                 status='In Use', location='London HQ - Floor 2',
                 purchase_date=date(2023, 3, 15), purchase_cost=549.00,
                 warranty_expiry=date(2026, 3, 15), assigned_to_id=alice.id),

            dict(name='iPhone 14 Pro', asset_tag='MOB-001', asset_type='Mobile',
                 manufacturer='Apple', model='iPhone 14 Pro',
                 serial_number='SN-IPHONE-001',
                 status='In Use', location='London HQ',
                 purchase_date=date(2022, 10, 1), purchase_cost=999.00,
                 warranty_expiry=date(2024, 10, 1), assigned_to_id=admin.id),

            dict(name='Adobe Creative Cloud (10 seats)', asset_tag='SW-001',
                 asset_type='Software Licence',
                 manufacturer='Adobe', model='Creative Cloud All Apps',
                 serial_number='LIC-ADOBE-CC-2024',
                 status='In Use', location='N/A',
                 purchase_date=date(2024, 1, 1), purchase_cost=5990.00,
                 warranty_expiry=date(2025, 1, 1),
                 notes='Annual subscription. Renewal due Jan 2025.'),

            dict(name='HP LaserJet Pro M404dn', asset_tag='PRN-001', asset_type='Printer',
                 manufacturer='HP', model='LaserJet Pro M404dn',
                 serial_number='SN-HPPRN-001',
                 status='Under Repair', location='London HQ - Floor 2',
                 purchase_date=date(2021, 9, 12), purchase_cost=299.00,
                 notes='Paper jam issue. Sent for repair 2024-10-01.'),

            dict(name='Logitech MX Keys Keyboard', asset_tag='PER-001',
                 asset_type='Peripheral',
                 manufacturer='Logitech', model='MX Keys',
                 serial_number='SN-LOGI-001',
                 status='In Use', location='London HQ - Floor 3',
                 purchase_date=date(2023, 5, 20), purchase_cost=109.00,
                 assigned_to_id=bob.id),

            dict(name='Dell XPS 13 (Old)', asset_tag='LT-003', asset_type='Laptop',
                 manufacturer='Dell', model='XPS 13 9310',
                 serial_number='SN-DELL-003',
                 status='Decommissioned', location='IT Storage Room',
                 purchase_date=date(2019, 2, 14), purchase_cost=1149.00,
                 notes='End of life. Data wiped. Awaiting disposal.'),

            dict(name='Microsoft 365 Business (50 seats)', asset_tag='SW-002',
                 asset_type='Software Licence',
                 manufacturer='Microsoft', model='Microsoft 365 Business Premium',
                 serial_number='LIC-MS365-2024',
                 status='In Use', location='N/A',
                 purchase_date=date(2024, 4, 1), purchase_cost=7500.00,
                 warranty_expiry=date(2025, 4, 1),
                 notes='Company-wide Microsoft 365 subscription.'),
        ]

        asset_objects = []
        for data in assets_data:
            a = Asset(**data)
            db.session.add(a)
            asset_objects.append(a)

        db.session.flush()

        # ── Tickets ──────────────────────────────────────────────────── #
        print('🎫 Creating tickets...')

        tickets_data = [
            dict(title='Laptop running very slowly since Windows update',
                 description='Since the Windows 11 update last Tuesday my laptop has been '
                             'extremely slow to boot and applications take ages to open. '
                             'I have tried restarting multiple times.\n\nAsset: LT-001',
                 status='In Progress', priority='High', category='Hardware',
                 raised_by_id=alice.id, assigned_to_id=admin.id,
                 related_asset_id=asset_objects[0].id,
                 created_at=datetime.utcnow() - timedelta(days=5)),

            dict(title='Cannot access shared Finance drive',
                 description='I am getting "Access Denied" when trying to open '
                             '\\\\fileserver\\Finance since this morning. I was able '
                             'to access it yesterday. Other colleagues in Finance can '
                             'still access it.',
                 status='Open', priority='Critical', category='Account Access',
                 raised_by_id=alice.id,
                 created_at=datetime.utcnow() - timedelta(days=1)),

            dict(title='Outlook keeps crashing when opening attachments',
                 description='Microsoft Outlook crashes every time I try to open '
                             'a PDF attachment. I have tried with several different '
                             'emails and it happens consistently. Running Outlook 2021.',
                 status='Open', priority='Medium', category='Software',
                 raised_by_id=bob.id,
                 created_at=datetime.utcnow() - timedelta(days=2)),

            dict(title='Printer on Floor 2 showing offline',
                 description='The HP printer (PRN-001) on Floor 2 is showing as '
                             'offline. I have checked the network cable which appears '
                             'to be plugged in. Other printers are working fine.',
                 status='Resolved', priority='Low', category='Printer',
                 raised_by_id=carol.id, assigned_to_id=admin.id,
                 related_asset_id=asset_objects[8].id,
                 resolution_notes='Printer was under repair. Replacement toner installed '
                                  'and firmware updated. Printer now back online.',
                 created_at=datetime.utcnow() - timedelta(days=10),
                 resolved_at=datetime.utcnow() - timedelta(days=8)),

            dict(title='Request new monitor for dual-screen setup',
                 description='I would like to request an additional monitor to enable '
                             'a dual-screen setup. My work involves reviewing large '
                             'spreadsheets and having a second screen would significantly '
                             'improve my productivity.',
                 status='Closed', priority='Low', category='Hardware',
                 raised_by_id=alice.id, assigned_to_id=admin.id,
                 resolution_notes='Second monitor (MON-001) allocated and configured.',
                 created_at=datetime.utcnow() - timedelta(days=30),
                 resolved_at=datetime.utcnow() - timedelta(days=25)),

            dict(title='Suspected phishing email received',
                 description='I received a suspicious email claiming to be from our '
                             'bank asking me to verify my account details. I did not '
                             'click any links. Email is from: support@bank-secure-verify.ru\n\n'
                             'Please advise on next steps.',
                 status='In Progress', priority='Critical', category='Security Incident',
                 raised_by_id=bob.id, assigned_to_id=admin.id,
                 created_at=datetime.utcnow() - timedelta(hours=6)),

            dict(title='VPN not connecting from home',
                 description='Since changing my home router I cannot connect to the '
                             'company VPN. I get error: "The remote connection was not '
                             'made because the name of the remote access server did not '
                             'resolve." My internet connection is working normally.',
                 status='Open', priority='High', category='Network',
                 raised_by_id=carol.id,
                 created_at=datetime.utcnow() - timedelta(days=3)),

            dict(title='Adobe Photoshop licence error',
                 description='When opening Photoshop I get the error: "Your account '
                             'does not have an active subscription for Adobe Photoshop". '
                             'This started happening after I logged out and back in to '
                             'Creative Cloud.',
                 status='Open', priority='Medium', category='Software',
                 raised_by_id=alice.id,
                 related_asset_id=asset_objects[7].id,
                 created_at=datetime.utcnow() - timedelta(days=1)),

            dict(title='Password reset request for new starter',
                 description='New team member James Taylor (james.taylor@secureit.local) '
                             'started today and cannot log in. Please could you reset '
                             'their password.',
                 status='Resolved', priority='Medium', category='Account Access',
                 raised_by_id=carol.id, assigned_to_id=admin.id,
                 resolution_notes='Temporary password issued. User confirmed able to log in.',
                 created_at=datetime.utcnow() - timedelta(days=7),
                 resolved_at=datetime.utcnow() - timedelta(days=7)),

            dict(title='Network very slow in meeting room B',
                 description='The WiFi in meeting room B is extremely slow during '
                             'video calls. Other meeting rooms are fine. This has been '
                             'happening for the past week and is affecting our client '
                             'calls.',
                 status='In Progress', priority='High', category='Network',
                 raised_by_id=bob.id, assigned_to_id=admin.id,
                 created_at=datetime.utcnow() - timedelta(days=7)),
        ]

        ticket_objects = []
        for data in tickets_data:
            t = Ticket(**data)
            db.session.add(t)
            ticket_objects.append(t)

        db.session.flush()

        # ── Comments ─────────────────────────────────────────────────── #
        print('💬 Creating comments...')

        comments = [
            Comment(ticket_id=ticket_objects[0].id, author_id=admin.id,
                    body='I have run diagnostics remotely. The system is showing high CPU usage '
                         'from Windows Update service. I will schedule a maintenance window '
                         'to apply the updates properly and clear the cache.',
                    is_internal=False,
                    created_at=datetime.utcnow() - timedelta(days=4)),

            Comment(ticket_id=ticket_objects[0].id, author_id=admin.id,
                    body='INTERNAL: Possible driver conflict with update KB5031354. '
                         'Check Device Manager for yellow exclamation marks.',
                    is_internal=True,
                    created_at=datetime.utcnow() - timedelta(days=4)),

            Comment(ticket_id=ticket_objects[0].id, author_id=alice.id,
                    body='Thank you for looking into this. Let me know when you need to '
                         'access the machine for the maintenance window.',
                    created_at=datetime.utcnow() - timedelta(days=3)),

            Comment(ticket_id=ticket_objects[5].id, author_id=admin.id,
                    body='Thank you for reporting this. Please do NOT click any links '
                         'in the email. I have flagged this to our security team and '
                         'will quarantine the email from your mailbox.',
                    created_at=datetime.utcnow() - timedelta(hours=5)),

            Comment(ticket_id=ticket_objects[5].id, author_id=admin.id,
                    body='INTERNAL: Email header analysis shows originating IP: 45.142.212.100 '
                         '(RU). SPF and DKIM both fail. Updating email filter rules.',
                    is_internal=True,
                    created_at=datetime.utcnow() - timedelta(hours=4)),

            Comment(ticket_id=ticket_objects[9].id, author_id=admin.id,
                    body='I have checked the access point in meeting room B. '
                         'Channel utilisation is at 94% — there is significant '
                         'interference from nearby devices. I will change the '
                         'channel and increase the TX power.',
                    created_at=datetime.utcnow() - timedelta(days=5)),
        ]

        db.session.add_all(comments)

        # ── Audit log seed entries ────────────────────────────────────── #
        print('📋 Seeding audit log...')

        audit_entries = [
            AuditLog(user_id=admin.id, event_type=AuditLog.EVENT_LOGIN_SUCCESS,
                     description='Successful login: admin',
                     ip_address='192.168.1.100',
                     timestamp=datetime.utcnow() - timedelta(hours=2)),
            AuditLog(user_id=alice.id, event_type=AuditLog.EVENT_LOGIN_SUCCESS,
                     description='Successful login: alice.jones',
                     ip_address='192.168.1.101',
                     timestamp=datetime.utcnow() - timedelta(days=1)),
            AuditLog(user_id=None, event_type=AuditLog.EVENT_LOGIN_FAIL,
                     description='Failed login attempt for username: hacker123',
                     ip_address='10.0.0.55',
                     timestamp=datetime.utcnow() - timedelta(hours=12)),
            AuditLog(user_id=admin.id, event_type=AuditLog.EVENT_CREATE,
                     description='Asset created: LT-001 - Dell XPS 15 Laptop',
                     resource_type='Asset', resource_id=asset_objects[0].id,
                     ip_address='192.168.1.100',
                     timestamp=datetime.utcnow() - timedelta(days=200)),
        ]
        db.session.add_all(audit_entries)

        # ── Rental Catalog ────────────────────────────────────────────── #
        print('🎧 Creating rental catalog...')

        rental_items = [
            RentalItem(name='Sony WH-1000XM5 Headset', category='Headset',
                       description='Noise-cancelling wireless headset', quantity_total=4),
            RentalItem(name='Jabra Evolve2 55 Headset', category='Headset',
                       description='Teams-certified wireless headset', quantity_total=3),
            RentalItem(name='Logitech MX Keys Mini', category='Keyboard',
                       description='Compact wireless keyboard', quantity_total=5),
            RentalItem(name='Apple Magic Keyboard', category='Keyboard',
                       description='Bluetooth keyboard with Touch ID', quantity_total=3),
            RentalItem(name='Logitech MX Master 3', category='Mouse',
                       description='Ergonomic wireless mouse', quantity_total=6),
            RentalItem(name='Dell UltraSharp 24" Monitor', category='Monitor',
                       description='USB-C portable monitor for meetings', quantity_total=2),
            RentalItem(name='Logitech C920 Webcam', category='Webcam',
                       description='1080p HD webcam for video calls', quantity_total=4),
            RentalItem(name='USB-C Hub (7-in-1)', category='Cable / Adapter',
                       description='HDMI, USB-A x3, SD card, USB-C PD', quantity_total=8),
            RentalItem(name='HDMI to DisplayPort Adapter', category='Cable / Adapter',
                       description='For connecting to projectors and displays', quantity_total=6),
        ]
        db.session.add_all(rental_items)
        db.session.flush()

        # Sample active rental (alice has a headset)
        sample_rental = Rental(
            item_id=rental_items[0].id,
            user_id=alice.id,
            return_by=date.today(),
            notes='For the monthly Finance review meeting',
            status='Active',
            rented_at=datetime.utcnow() - timedelta(hours=3),
        )
        db.session.add(sample_rental)

        db.session.commit()

        print('\n✅ Database seeded successfully!')
        print('\n📋 Test Credentials:')
        print('   Admin  : admin / Admin@12345')
        print('   User 1 : alice.jones / Alice@12345')
        print('   User 2 : bob.smith / Bob@123456')
        print('   User 3 : carol.white / Carol@1234')
        print('   (dave.brown is deactivated — try logging in to test)')


if __name__ == '__main__':
    seed_database()
