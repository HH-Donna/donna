from typing import List
from fastapi import HTTPException
from app.database.supabase_client import get_supabase_client
from app.models import BillerProfile
from datetime import datetime


async def save_biller_to_companies(user_uuid: str, biller: BillerProfile) -> dict:
    """
    Save or update a single biller profile to the companies table.
    """
    supabase = get_supabase_client()
    
    try:
        # Prepare data for insert/update
        # Calculate total_invoices from source_emails array
        total_invoices = len([e for e in biller.source_emails if e]) if biller.source_emails else 0
        
        company_data = {
            'user_id': user_uuid,
            'name': biller.full_name,
            'domain': biller.domain,
            'contact_email': biller.email_address,
            'billing_address': biller.full_address,
            'profile_picture_url': biller.profile_picture_url,
            'payment_method': biller.payment_method,
            'billing_info': biller.billing_info,
            'frequency': biller.frequency,
            'total_invoices': total_invoices,
            'source_email_ids': biller.source_emails,
            'updated_at': datetime.now().isoformat()
        }
        
        print(f"   📊 {biller.full_name}: {total_invoices} invoices from {len(biller.source_emails)} email IDs")
        
        # Use upsert to insert or update
        # Note: Supabase Python client doesn't support on_conflict parameter the same way
        # We'll use upsert() which automatically handles conflicts based on primary key
        # For user_id+domain uniqueness, we need to handle it differently
        
        # First, try to find existing company
        existing = supabase.table('companies')\
            .select('id')\
            .eq('user_id', user_uuid)\
            .eq('domain', company_data['domain'])\
            .execute()
        
        if existing.data and len(existing.data) > 0:
            # Update existing company
            company_id = existing.data[0]['id']
            response = supabase.table('companies')\
                .update(company_data)\
                .eq('id', company_id)\
                .execute()
        else:
            # Insert new company
            response = supabase.table('companies')\
                .insert(company_data)\
                .execute()
        
        if response.data:
            return {
                'success': True,
                'company_id': response.data[0].get('id'),
                'message': f'Saved {biller.full_name}'
            }
        else:
            return {
                'success': False,
                'message': f'Failed to save {biller.full_name}'
            }
            
    except Exception as e:
        error_msg = str(e)
        print(f"❌ Error saving biller {biller.full_name}: {error_msg}")
        import traceback
        traceback.print_exc()
        return {
            'success': False,
            'message': error_msg
        }


async def save_billers_to_companies(user_uuid: str, billers: List[BillerProfile]) -> dict:
    """
    Save multiple biller profiles to the companies table.
    """
    results = {
        'total': len(billers),
        'saved': 0,
        'failed': 0,
        'errors': []
    }
    
    print(f"💾 Starting to save {len(billers)} billers to database...")
    
    for idx, biller in enumerate(billers):
        print(f"   Saving {idx + 1}/{len(billers)}: {biller.full_name}")
        result = await save_biller_to_companies(user_uuid, biller)
        if result['success']:
            results['saved'] += 1
            print(f"   ✅ Saved {biller.full_name}")
        else:
            results['failed'] += 1
            results['errors'].append({
                'biller': biller.full_name,
                'error': result['message']
            })
            print(f"   ❌ Failed to save {biller.full_name}: {result['message']}")
    
    return results
