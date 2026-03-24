#!/usr/bin/env python3
"""
Database initialization script for MHRAS.

This script:
1. Creates the database if it doesn't exist
2. Runs database migrations
3. Seeds consent records for test patients
4. Seeds resource catalog (therapy, medication, crisis resources)
"""

import sys
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime, timedelta

from src.database.connection import DatabaseConnection
from src.database.migration_runner import MigrationRunner
from src.logging_config import setup_logging

setup_logging()
logger = logging.getLogger(__name__)


def create_database(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> bool:
    """
    Create the database if it doesn't exist.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        True if database was created or already exists
    """
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

    logger.info(f"Checking if database '{database}' exists...")

    try:
        # Connect to default postgres database to create our database
        conn = psycopg2.connect(
            host=host,
            port=port,
            database='postgres',
            user=user,
            password=password
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)

        cursor = conn.cursor()

        # Check if database exists
        cursor.execute(
            "SELECT 1 FROM pg_database WHERE datname = %s",
            (database,)
        )
        exists = cursor.fetchone() is not None

        if not exists:
            logger.info(f"Creating database '{database}'...")
            cursor.execute(f'CREATE DATABASE "{database}"')
            logger.info(f"✓ Database '{database}' created successfully")
        else:
            logger.info(f"✓ Database '{database}' already exists")

        cursor.close()
        conn.close()
        return True

    except Exception as e:
        logger.error(f"✗ Failed to create database: {e}")
        return False


def run_migrations(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> bool:
    """
    Run database migrations.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        True if migrations succeeded
    """
    logger.info("Running database migrations...")

    try:
        # Build database URL for MigrationRunner
        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

        runner = MigrationRunner(database_url)
        applied = runner.run_migrations()

        if applied > 0:
            logger.info(f"✓ Applied {applied} migrations successfully")
        else:
            logger.info("✓ No new migrations to apply")
        return True

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        return False


def seed_consent_records(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> bool:
    """
    Seed consent records for test patients.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        True if seeding succeeded
    """
    logger.info("Seeding consent records...")

    try:
        import psycopg2

        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        conn = psycopg2.connect(database_url)

        # Test patient IDs
        test_patients = [
            'test_patient_001',
            'test_patient_002',
            'demo_patient_001',
            'demo_patient_002'
        ]

        now = datetime.utcnow()
        expires_at = now + timedelta(days=365)

        cursor = conn.cursor()

        for patient_id in test_patients:
            cursor.execute("""
                INSERT INTO consent (anonymized_id, data_types, granted_at, expires_at)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (anonymized_id) DO UPDATE
                SET data_types = EXCLUDED.data_types,
                    granted_at = EXCLUDED.granted_at,
                    expires_at = EXCLUDED.expires_at,
                    revoked_at = NULL
            """, (
                patient_id,
                ['survey', 'wearable', 'emr'],
                now,
                expires_at
            ))
            logger.info(f"  ✓ Created/updated consent for {patient_id}")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("✓ Consent records seeded successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to seed consent records: {e}")
        return False


def seed_resource_catalog(
    host: str,
    port: int,
    database: str,
    user: str,
    password: str
) -> bool:
    """
    Seed resource catalog with mental health resources.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password

    Returns:
        True if seeding succeeded
    """
    logger.info("Seeding resource catalog...")

    try:
        import psycopg2
        import json

        database_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"
        conn = psycopg2.connect(database_url)
        cursor = conn.cursor()

        # Define resources matching the schema
        resources = [
            # Crisis Resources
            {
                'id': 'crisis_988',
                'resource_type': 'crisis_line',
                'name': '988 Suicide & Crisis Lifeline',
                'description': '24/7 crisis support for anyone in distress. Call or text 988 for immediate help.',
                'contact_info': 'Call or Text: 988',
                'urgency': 'immediate',
                'eligibility_criteria': json.dumps({'age': ['all'], 'insurance': ['any']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH', 'CRITICAL']),
                'tags': json.dumps(['crisis', 'immediate', 'suicide-prevention', 'free']),
                'priority': 100
            },
            {
                'id': 'crisis_text_line',
                'resource_type': 'crisis_line',
                'name': 'Crisis Text Line',
                'description': 'Text-based crisis support. Text HOME to 741741 to connect with a counselor.',
                'contact_info': 'Text HOME to 741741',
                'urgency': 'immediate',
                'eligibility_criteria': json.dumps({'age': ['youth', 'young_adult'], 'insurance': ['any']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH', 'CRITICAL']),
                'tags': json.dumps(['crisis', 'text', 'youth', 'free']),
                'priority': 100
            },
            {
                'id': 'crisis_nami',
                'resource_type': 'crisis_line',
                'name': 'NAMI Helpline',
                'description': 'Crisis helpline providing support, information, and resources for mental health.',
                'contact_info': '1-800-950-6264 (NAMI)',
                'urgency': 'immediate',
                'eligibility_criteria': json.dumps({'age': ['all'], 'insurance': ['any']}),
                'risk_levels': json.dumps(['MODERATE', 'HIGH', 'CRITICAL']),
                'tags': json.dumps(['crisis', 'information', 'support', 'free']),
                'priority': 90
            },
            {
                'id': 'crisis_samhsa',
                'resource_type': 'crisis_line',
                'name': 'SAMHSA National Helpline',
                'description': 'Treatment referral and information service for mental health and substance use disorders.',
                'contact_info': '1-800-662-4357 (HELP)',
                'urgency': 'immediate',
                'eligibility_criteria': json.dumps({'age': ['all'], 'insurance': ['any']}),
                'risk_levels': json.dumps(['MODERATE', 'HIGH', 'CRITICAL']),
                'tags': json.dumps(['crisis', 'referral', 'substance-use', 'free']),
                'priority': 90
            },

            # Therapy Resources
            {
                'id': 'therapy_cbt',
                'resource_type': 'therapy',
                'name': 'Cognitive Behavioral Therapy (CBT)',
                'description': 'Evidence-based therapy focusing on identifying and changing negative thought patterns and behaviors.',
                'contact_info': 'Contact local mental health provider',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['depression', 'anxiety', 'PTSD']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH']),
                'tags': json.dumps(['therapy', 'evidence-based', 'cognitive', 'insurance']),
                'priority': 50
            },
            {
                'id': 'therapy_dbt',
                'resource_type': 'therapy',
                'name': 'Dialectical Behavior Therapy (DBT)',
                'description': 'Therapy focused on emotional regulation and interpersonal effectiveness.',
                'contact_info': 'Contact local mental health provider',
                'urgency': 'soon',
                'eligibility_criteria': json.dumps({'conditions': ['borderline', 'self-harm', 'emotional-dysregulation']}),
                'risk_levels': json.dumps(['HIGH', 'CRITICAL']),
                'tags': json.dumps(['therapy', 'emotional-regulation', 'skills', 'insurance']),
                'priority': 60
            },
            {
                'id': 'therapy_act',
                'resource_type': 'therapy',
                'name': 'Acceptance and Commitment Therapy (ACT)',
                'description': 'Therapy focusing on accepting difficult emotions while committing to value-driven actions.',
                'contact_info': 'Contact local mental health provider',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['anxiety', 'depression', 'chronic-pain', 'stress']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH']),
                'tags': json.dumps(['therapy', 'acceptance', 'values', 'insurance']),
                'priority': 40
            },
            {
                'id': 'therapy_mbsr',
                'resource_type': 'therapy',
                'name': 'Mindfulness-Based Stress Reduction (MBSR)',
                'description': '8-week program using mindfulness to help manage stress and chronic conditions.',
                'contact_info': 'Contact local hospital or wellness center',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['stress', 'chronic-pain', 'anxiety']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE']),
                'tags': json.dumps(['therapy', 'mindfulness', 'stress-reduction', 'wellness']),
                'priority': 30
            },

            # Support Groups
            {
                'id': 'support_nami',
                'resource_type': 'support_group',
                'name': 'NAMI Support Groups',
                'description': 'Peer-led support groups for individuals living with mental illness and their families.',
                'contact_info': 'Find at nami.org/find-support',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['mental-illness'], 'family': ['allowed']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH']),
                'tags': json.dumps(['support-group', 'peer', 'family', 'free']),
                'priority': 40
            },
            {
                'id': 'support_dbsa',
                'resource_type': 'support_group',
                'name': 'Depression and Bipolar Support Alliance',
                'description': 'Peer-based wellness models and support groups for depression and bipolar disorder.',
                'contact_info': 'Find at dbsalliance.org/support',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['depression', 'bipolar']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE', 'HIGH']),
                'tags': json.dumps(['support-group', 'peer', 'depression', 'bipolar', 'free']),
                'priority': 40
            },
            {
                'id': 'support_adaa',
                'resource_type': 'support_group',
                'name': 'ADAA Online Support Groups',
                'description': 'Online support groups and resources for anxiety and depression.',
                'contact_info': 'Find at adaa.org',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['anxiety', 'depression']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE']),
                'tags': json.dumps(['support-group', 'online', 'anxiety', 'depression', 'free']),
                'priority': 30
            },

            # Medication Resources
            {
                'id': 'med_psych_eval',
                'resource_type': 'medication',
                'name': 'Psychiatric Medication Consultation',
                'description': 'Consultation with a psychiatrist for medication evaluation and management.',
                'contact_info': 'Contact local psychiatric provider',
                'urgency': 'soon',
                'eligibility_criteria': json.dumps({'conditions': ['depression', 'anxiety', 'bipolar', 'psychosis']}),
                'risk_levels': json.dumps(['MODERATE', 'HIGH', 'CRITICAL']),
                'tags': json.dumps(['medication', 'psychiatry', 'evaluation', 'insurance']),
                'priority': 50
            },

            # Wellness/Lifestyle Resources
            {
                'id': 'wellness_exercise',
                'resource_type': 'wellness',
                'name': 'Exercise and Physical Activity Programs',
                'description': 'Programs promoting physical activity as a tool for mental health improvement.',
                'contact_info': 'Contact local gym, community center, or healthcare provider',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'age': ['all']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE']),
                'tags': json.dumps(['lifestyle', 'exercise', 'wellness', 'community']),
                'priority': 20
            },
            {
                'id': 'wellness_sleep',
                'resource_type': 'wellness',
                'name': 'Sleep Hygiene Education',
                'description': 'Education and counseling on improving sleep habits for better mental health.',
                'contact_info': 'Contact healthcare provider or sleep clinic',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'conditions': ['sleep-difficulties']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE']),
                'tags': json.dumps(['lifestyle', 'sleep', 'education', 'insurance']),
                'priority': 25
            },
            {
                'id': 'wellness_mindfulness_app',
                'resource_type': 'self_help',
                'name': 'Mindfulness and Meditation Apps',
                'description': 'Apps and programs for daily mindfulness and meditation practice.',
                'contact_info': 'Various apps (Headspace, Calm, Insight Timer, etc.)',
                'urgency': 'routine',
                'eligibility_criteria': json.dumps({'age': ['all']}),
                'risk_levels': json.dumps(['LOW', 'MODERATE']),
                'tags': json.dumps(['lifestyle', 'mindfulness', 'app', 'self-help', 'free']),
                'priority': 15
            },

            # Emergency Resources
            {
                'id': 'emergency_911',
                'resource_type': 'emergency',
                'name': 'Emergency Services (911)',
                'description': 'For immediate life-threatening emergencies requiring police, fire, or ambulance.',
                'contact_info': 'Call 911',
                'urgency': 'immediate',
                'eligibility_criteria': json.dumps({'emergency': ['life-threatening']}),
                'risk_levels': json.dumps(['CRITICAL']),
                'tags': json.dumps(['emergency', 'immediate', 'life-threatening', 'free']),
                'priority': 100
            }
        ]

        # Insert resources
        for resource in resources:
            cursor.execute("""
                INSERT INTO resources (
                    id, resource_type, name, description, contact_info,
                    urgency, eligibility_criteria, risk_levels, tags, priority
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO UPDATE
                SET resource_type = EXCLUDED.resource_type,
                    name = EXCLUDED.name,
                    description = EXCLUDED.description,
                    contact_info = EXCLUDED.contact_info,
                    urgency = EXCLUDED.urgency,
                    eligibility_criteria = EXCLUDED.eligibility_criteria,
                    risk_levels = EXCLUDED.risk_levels,
                    tags = EXCLUDED.tags,
                    priority = EXCLUDED.priority,
                    active = TRUE
            """, (
                resource['id'],
                resource['resource_type'],
                resource['name'],
                resource['description'],
                resource['contact_info'],
                resource['urgency'],
                resource['eligibility_criteria'],
                resource['risk_levels'],
                resource['tags'],
                resource['priority']
            ))
            logger.info(f"  ✓ Added resource: {resource['name']}")

        conn.commit()
        cursor.close()
        conn.close()

        logger.info("✓ Resource catalog seeded successfully")
        return True

    except Exception as e:
        logger.error(f"✗ Failed to seed resource catalog: {e}")
        return False


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description='Initialize MHRAS database')
    parser.add_argument('--host', default='localhost', help='Database host')
    parser.add_argument('--port', type=int, default=5432, help='Database port')
    parser.add_argument('--database', default='mhras', help='Database name')
    parser.add_argument('--user', default='postgres', help='Database user')
    parser.add_argument('--password', default=None, help='Database password (will prompt if not provided)')
    parser.add_argument('--skip-consent', action='store_true', help='Skip seeding consent records')
    parser.add_argument('--skip-resources', action='store_true', help='Skip seeding resource catalog')
    parser.add_argument('--migrations-only', action='store_true', help='Only run migrations')
    parser.add_argument('--create-db', action='store_true', help='Create database if it does not exist')

    args = parser.parse_args()

    # Prompt for password if not provided
    password = args.password
    if password is None:
        import getpass
        password = getpass.getpass('Database password: ')

    # Create database if requested
    if args.create_db:
        if not create_database(args.host, args.port, args.database, args.user, password):
            logger.error("Database creation failed, aborting")
            return 1

    # Run migrations
    if not run_migrations(args.host, args.port, args.database, args.user, password):
        logger.error("Migrations failed, aborting")
        return 1

    # Skip seeding if requested
    if args.migrations_only:
        logger.info("Migrations only requested, skipping seeding")
        return 0

    # Seed consent records
    if not args.skip_consent:
        if not seed_consent_records(args.host, args.port, args.database, args.user, password):
            logger.warning("Consent seeding failed, continuing...")

    # Seed resource catalog
    if not args.skip_resources:
        if not seed_resource_catalog(args.host, args.port, args.database, args.user, password):
            logger.warning("Resource catalog seeding failed, continuing...")

    logger.info("\n" + "=" * 60)
    logger.info("✓ Database initialization complete!")
    logger.info("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
