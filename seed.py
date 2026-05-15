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
            # ── Headsets ──────────────────────────────────────────────── #
            RentalItem(name='Sony WH-1000XM5', category='Headset', location='London',
                       description='Premium noise-cancelling wireless headset', quantity_total=20),
            RentalItem(name='Jabra Evolve2 85', category='Headset', location='London',
                       description='Teams-certified ANC wireless headset', quantity_total=20),
            RentalItem(name='Bose QuietComfort 45', category='Headset', location='London',
                       description='Comfortable all-day noise-cancelling headset', quantity_total=20),
            RentalItem(name='Sennheiser HD 450BT', category='Headset', location='Hove',
                       description='Lightweight Bluetooth headset with ANC', quantity_total=20),
            RentalItem(name='Jabra Evolve2 55', category='Headset', location='Hove',
                       description='Wireless on-ear headset for open offices', quantity_total=20),
            RentalItem(name='Sony WH-CH720N', category='Headset', location='Cardiff',
                       description='Lightweight noise-cancelling headset', quantity_total=20),
            RentalItem(name='Logitech H800', category='Headset', location='Cardiff',
                       description='Wireless stereo headset with USB dongle', quantity_total=20),

            # ── Keyboards ─────────────────────────────────────────────── #
            RentalItem(name='Logitech MX Keys', category='Keyboard', location='London',
                       description='Full-size backlit wireless keyboard', quantity_total=20),
            RentalItem(name='Apple Magic Keyboard', category='Keyboard', location='London',
                       description='Bluetooth keyboard with Touch ID', quantity_total=20),
            RentalItem(name='Microsoft Sculpt Ergonomic', category='Keyboard', location='London',
                       description='Split ergonomic wireless keyboard', quantity_total=20),
            RentalItem(name='Keychron K2 (Wireless)', category='Keyboard', location='Hove',
                       description='Compact mechanical keyboard, Bluetooth', quantity_total=20),
            RentalItem(name='Logitech MX Keys Mini', category='Keyboard', location='Hove',
                       description='Compact backlit wireless keyboard', quantity_total=20),
            RentalItem(name='Dell KB700 Multi-Device', category='Keyboard', location='Cardiff',
                       description='Compact wireless keyboard, multi-device', quantity_total=20),
            RentalItem(name='HP 350 Compact Multi-Device', category='Keyboard', location='Cardiff',
                       description='Slim Bluetooth keyboard', quantity_total=20),

            # ── Mice ──────────────────────────────────────────────────── #
            RentalItem(name='Logitech MX Master 3S', category='Mouse', location='London',
                       description='Ergonomic wireless mouse, ultra-precise', quantity_total=20),
            RentalItem(name='Apple Magic Mouse', category='Mouse', location='London',
                       description='Multi-touch wireless mouse', quantity_total=20),
            RentalItem(name='Microsoft Arc Mouse', category='Mouse', location='London',
                       description='Folding Bluetooth travel mouse', quantity_total=20),
            RentalItem(name='Logitech M750', category='Mouse', location='Hove',
                       description='Slim wireless mouse, multi-device', quantity_total=20),
            RentalItem(name='Razer Pro Click Mini', category='Mouse', location='Hove',
                       description='Compact ergonomic wireless mouse', quantity_total=20),
            RentalItem(name='HP 710 Rechargeable Silent', category='Mouse', location='Cardiff',
                       description='Quiet wireless mouse, USB-C charging', quantity_total=20),
            RentalItem(name='Logitech Signature M650', category='Mouse', location='Cardiff',
                       description='Comfortable silent wireless mouse', quantity_total=20),

            # ── Webcams ───────────────────────────────────────────────── #
            RentalItem(name='Logitech C930e', category='Webcam', location='London',
                       description='Full HD 1080p business webcam', quantity_total=20),
            RentalItem(name='Logitech Brio 500', category='Webcam', location='London',
                       description='Full HD webcam with auto-light correction', quantity_total=20),
            RentalItem(name='Microsoft Modern Webcam', category='Webcam', location='London',
                       description='1080p HDR certified for Teams', quantity_total=20),
            RentalItem(name='Razer Kiyo Pro', category='Webcam', location='Hove',
                       description='1080p adaptive light sensor webcam', quantity_total=20),
            RentalItem(name='Logitech C920 HD Pro', category='Webcam', location='Hove',
                       description='1080p HD webcam, dual mics', quantity_total=20),
            RentalItem(name='Anker PowerConf C300', category='Webcam', location='Cardiff',
                       description='Smart AI webcam, 1080p', quantity_total=20),
            RentalItem(name='Dell UltraSharp Webcam', category='Webcam', location='Cardiff',
                       description='4K Sony STARVIS sensor webcam', quantity_total=20),

            # ── Laptops ───────────────────────────────────────────────── #
            RentalItem(name='MacBook Air M2 13"', category='Laptop', location='London',
                       description='Apple M2 chip, 8GB RAM, 256GB SSD', quantity_total=20),
            RentalItem(name='Dell XPS 13 (Rental)', category='Laptop', location='London',
                       description='Intel Core i7, 16GB RAM, 512GB SSD', quantity_total=20),
            RentalItem(name='Lenovo ThinkPad X1 Carbon', category='Laptop', location='London',
                       description='Lightweight business laptop, 14"', quantity_total=20),
            RentalItem(name='HP EliteBook 840 G10', category='Laptop', location='Hove',
                       description='14" business laptop, Intel i5', quantity_total=20),
            RentalItem(name='Microsoft Surface Laptop 5', category='Laptop', location='Hove',
                       description='13.5" touchscreen, Intel i5, 8GB', quantity_total=20),
            RentalItem(name='MacBook Pro 14" M3', category='Laptop', location='Cardiff',
                       description='Apple M3 chip, 16GB RAM, 512GB SSD', quantity_total=20),
            RentalItem(name='Lenovo IdeaPad Flex 5', category='Laptop', location='Cardiff',
                       description='2-in-1 convertible laptop, AMD Ryzen 5', quantity_total=20),

            # ── Tablets ───────────────────────────────────────────────── #
            RentalItem(name='iPad Air (M2)', category='Tablet', location='London',
                       description='11" Apple iPad Air with USB-C', quantity_total=20),
            RentalItem(name='iPad Pro 11" (M4)', category='Tablet', location='London',
                       description='Pro tablet with ProMotion display', quantity_total=20),
            RentalItem(name='Samsung Galaxy Tab S9', category='Tablet', location='London',
                       description='Android tablet, 11", 256GB', quantity_total=20),
            RentalItem(name='Microsoft Surface Pro 9', category='Tablet', location='Hove',
                       description='Windows 2-in-1 tablet, Intel i5', quantity_total=20),
            RentalItem(name='Samsung Galaxy Tab S9 FE', category='Tablet', location='Hove',
                       description='Android tablet, 10.9", 128GB', quantity_total=20),
            RentalItem(name='iPad (10th Gen)', category='Tablet', location='Cardiff',
                       description='Standard iPad, 10.9", USB-C', quantity_total=20),
            RentalItem(name='Lenovo Tab P12 Pro', category='Tablet', location='Cardiff',
                       description='12.6" AMOLED Android tablet', quantity_total=20),

            # ── Phones ────────────────────────────────────────────────── #
            RentalItem(name='iPhone 15 Pro', category='Phone', location='London',
                       description='Apple iPhone 15 Pro, unlocked', quantity_total=20),
            RentalItem(name='Samsung Galaxy S24', category='Phone', location='London',
                       description='Android flagship, unlocked', quantity_total=20),
            RentalItem(name='Google Pixel 8', category='Phone', location='London',
                       description='Google Android phone, unlocked', quantity_total=20),
            RentalItem(name='iPhone 14', category='Phone', location='Hove',
                       description='Apple iPhone 14, unlocked', quantity_total=20),
            RentalItem(name='Samsung Galaxy A54', category='Phone', location='Hove',
                       description='Mid-range Android, unlocked', quantity_total=20),
            RentalItem(name='iPhone SE (3rd Gen)', category='Phone', location='Cardiff',
                       description='Compact Apple iPhone, unlocked', quantity_total=20),
            RentalItem(name='Motorola Edge 40', category='Phone', location='Cardiff',
                       description='5G Android phone, unlocked', quantity_total=20),

            # ── Cables / Adapters ─────────────────────────────────────── #
            RentalItem(name='USB-C Hub 7-in-1', category='Cable / Adapter', location='London',
                       description='HDMI 4K, USB-A x3, SD, USB-C PD 100W', quantity_total=20),
            RentalItem(name='HDMI to DisplayPort Adapter', category='Cable / Adapter', location='London',
                       description='For projectors and external displays', quantity_total=20),
            RentalItem(name='USB-C to HDMI Cable (2m)', category='Cable / Adapter', location='London',
                       description='Direct USB-C to HDMI, 4K@60Hz', quantity_total=20),
            RentalItem(name='Thunderbolt 4 Dock', category='Cable / Adapter', location='Hove',
                       description='12-in-1 docking station, dual 4K', quantity_total=20),
            RentalItem(name='USB-C to USB-A Adapter', category='Cable / Adapter', location='Hove',
                       description='Pack of 2 USB-C to USB-A adapters', quantity_total=20),
            RentalItem(name='Mini DisplayPort to HDMI', category='Cable / Adapter', location='Cardiff',
                       description='For older MacBooks and Surface devices', quantity_total=20),
            RentalItem(name='USB-C Multiport Adapter', category='Cable / Adapter', location='Cardiff',
                       description='HDMI, 2x USB-A, SD card reader', quantity_total=20),

            # ── Additional Headsets ────────────────────────────────────── #
            RentalItem(name='Dell Pro Stereo Headset UC350', category='Headset', location='London',
                       description='Dell wired USB headset, certified for UC platforms', quantity_total=20),
            RentalItem(name='Dell Speakerphone SP20', category='Headset', location='Hove',
                       description='Portable speakerphone for desk and meeting rooms', quantity_total=20),
            RentalItem(name='Poly Voyager Focus 2', category='Headset', location='Cardiff',
                       description='Wireless headset with active noise cancellation', quantity_total=20),
            RentalItem(name='Plantronics Blackwire 5220', category='Headset', location='London',
                       description='Stereo wired USB-A headset', quantity_total=20),

            # ── Additional Keyboards ───────────────────────────────────── #
            RentalItem(name='Dell KB900 Premier Collaboration', category='Keyboard', location='London',
                       description='Dell wireless keyboard with built-in Teams button', quantity_total=20),
            RentalItem(name='Dell KM7120W Multi-Device', category='Keyboard', location='Hove',
                       description='Dell wireless keyboard and mouse combo, multi-device', quantity_total=20),
            RentalItem(name='Logitech K780 Multi-Device', category='Keyboard', location='Cardiff',
                       description='Full-size wireless keyboard for desktop, tablet, phone', quantity_total=20),
            RentalItem(name='Microsoft Bluetooth Keyboard', category='Keyboard', location='London',
                       description='Slim Bluetooth keyboard with number pad', quantity_total=20),

            # ── Additional Mice ────────────────────────────────────────── #
            RentalItem(name='Dell MS900 Premier Rechargeable', category='Mouse', location='London',
                       description='Dell premium wireless mouse, USB-C rechargeable', quantity_total=20),
            RentalItem(name='Dell MS5120W Multi-Device', category='Mouse', location='Hove',
                       description='Dell compact wireless mouse, connects up to 3 devices', quantity_total=20),
            RentalItem(name='Logitech MX Anywhere 3', category='Mouse', location='Cardiff',
                       description='Compact wireless mouse, works on any surface', quantity_total=20),
            RentalItem(name='Microsoft Bluetooth Mouse', category='Mouse', location='London',
                       description='Slim Bluetooth mouse with scroll wheel', quantity_total=20),

            # ── Additional Webcams ─────────────────────────────────────── #
            RentalItem(name='Dell Pro 2K QHD Webcam WB3023', category='Webcam', location='London',
                       description='Dell 2K QHD webcam with AI auto-framing', quantity_total=20),
            RentalItem(name='Dell UltraSharp 4K Webcam WB7022', category='Webcam', location='Hove',
                       description='Dell 4K Sony STARVIS sensor, AI auto-framing', quantity_total=20),
            RentalItem(name='Poly Studio P5', category='Webcam', location='Cardiff',
                       description='Professional 1080p webcam with Poly Lens software', quantity_total=20),
            RentalItem(name='Elgato Facecam Pro', category='Webcam', location='London',
                       description='4K60 full-frame webcam, fixed focus', quantity_total=20),

            # ── Additional Laptops ─────────────────────────────────────── #
            RentalItem(name='Dell Latitude 7440', category='Laptop', location='London',
                       description='Dell business laptop, Intel Core i7, 16GB RAM', quantity_total=20),
            RentalItem(name='Dell XPS 15 (Rental)', category='Laptop', location='Hove',
                       description='Dell XPS 15, Intel Core i9, OLED display', quantity_total=20),
            RentalItem(name='Dell Inspiron 14 2-in-1', category='Laptop', location='Cardiff',
                       description='Dell convertible laptop, AMD Ryzen 7, touchscreen', quantity_total=20),
            RentalItem(name='Asus ZenBook 14', category='Laptop', location='London',
                       description='Ultra-slim laptop, Intel Core i5, 14" OLED', quantity_total=20),

            # ── Additional Tablets ─────────────────────────────────────── #
            RentalItem(name='Samsung Galaxy Tab S9 Ultra', category='Tablet', location='London',
                       description='14.6" flagship Android tablet, S Pen included', quantity_total=20),
            RentalItem(name='Microsoft Surface Go 3', category='Tablet', location='Hove',
                       description='Compact Windows 2-in-1, 10.5", Intel Pentium', quantity_total=20),
            RentalItem(name='iPad mini (6th Gen)', category='Tablet', location='Cardiff',
                       description='Compact Apple tablet, 8.3", USB-C', quantity_total=20),
            RentalItem(name='Lenovo Tab M10 Plus', category='Tablet', location='London',
                       description='10.6" Android tablet, 4GB RAM, 128GB', quantity_total=20),

            # ── Additional Phones ──────────────────────────────────────── #
            RentalItem(name='Samsung Galaxy S24 Ultra', category='Phone', location='London',
                       description='Samsung flagship with S Pen, unlocked', quantity_total=20),
            RentalItem(name='Google Pixel 8 Pro', category='Phone', location='Hove',
                       description='Google flagship Android phone, unlocked', quantity_total=20),
            RentalItem(name='OnePlus 12', category='Phone', location='Cardiff',
                       description='Flagship Android, 5G, unlocked', quantity_total=20),
            RentalItem(name='iPhone 15', category='Phone', location='London',
                       description='Apple iPhone 15, USB-C, unlocked', quantity_total=20),

            # ── Additional Cables / Adapters ───────────────────────────── #
            RentalItem(name='Dell DA300 Mobile Adapter', category='Cable / Adapter', location='London',
                       description='Dell 6-in-1 USB-C adapter: HDMI, VGA, DP, USB-A, RJ45, USB-C', quantity_total=20),
            RentalItem(name='Dell WD22TB4 Thunderbolt Dock', category='Cable / Adapter', location='Hove',
                       description='Dell 21-in-1 Thunderbolt 4 dock, dual 4K, 130W PD', quantity_total=20),
            RentalItem(name='USB-A to USB-C Cable (1m)', category='Cable / Adapter', location='Cardiff',
                       description='Fast-charge USB-A to USB-C cable, 60W', quantity_total=20),
            RentalItem(name='VGA to HDMI Adapter', category='Cable / Adapter', location='London',
                       description='For connecting to older projectors with VGA input', quantity_total=20),
        ]
        db.session.add_all(rental_items)
        db.session.flush()

        # Sample active rental (alice has a headset)
        sample_rental = Rental(
            item_id=rental_items[0].id,
            user_id=alice.id,
            return_by=date.today() + timedelta(days=1),
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
