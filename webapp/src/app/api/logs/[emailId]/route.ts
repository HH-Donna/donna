import { NextResponse } from 'next/server'
import { createClient } from '@/app/utils/supabase/server'

export async function GET(
  _req: Request,
  { params }: { params: { emailId: string } }
) {
  const supabase = await createClient()

  // Normalize ID to string (DB column email_id is TEXT)
  const emailId = String(params.emailId)

  const { data, error } = await supabase
    .from('email_fraud_logs')
    .select('step,decision,confidence,reasoning,details,created_at')
    .eq('email_id', emailId)
    .order('created_at', { ascending: true })

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ logs: data ?? [] })
}


