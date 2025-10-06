import { NextResponse } from 'next/server'
import { createClient } from '@/app/utils/supabase/server'

export async function GET(
  _req: Request,
  { params }: { params: { emailId: string } }
) {
  const supabase = await createClient()

  // The emailId param is the database ID, but fraud logs use gmail_message_id
  // First, get the gmail_message_id from the emails table
  const emailId = String(params.emailId)
  
  console.log('🔍 [API] Querying email database ID:', emailId)
  
  const { data: emailData, error: emailError } = await supabase
    .from('emails')
    .select('gmail_message_id')
    .eq('id', emailId)
    .single()
  
  console.log('📧 [API] Email query result:', emailData)
  
  if (emailError || !emailData?.gmail_message_id) {
    console.log('❌ [API] Email not found or no gmail_message_id:', emailError)
    return NextResponse.json({ logs: [] })
  }
  
  const gmailMessageId = emailData.gmail_message_id
  console.log('🔍 [API] Querying fraud logs for gmail_message_id:', gmailMessageId)

  const { data, error } = await supabase
    .from('email_fraud_logs')
    .select('step,decision,confidence,reasoning,details,created_at')
    .eq('email_id', gmailMessageId)
    .order('created_at', { ascending: true })

  console.log('📊 [API] Query result - data:', data)
  console.log('❌ [API] Query result - error:', error)
  console.log('📈 [API] Number of logs found:', data?.length || 0)

  if (error) {
    return NextResponse.json({ error: error.message }, { status: 500 })
  }

  return NextResponse.json({ logs: data ?? [] })
}


