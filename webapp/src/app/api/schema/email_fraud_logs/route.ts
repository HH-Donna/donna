import { NextResponse } from 'next/server'
import { createClient } from '@/app/utils/supabase/server'

type ColumnInfo = {
  column_name: string
  data_type?: string | null
  is_nullable?: string | null
  column_default?: string | null
  ordinal_position?: number | null
}

export async function GET() {
  const supabase = await createClient()

  // First attempt: query information_schema.columns directly (may not be exposed in some Supabase configs)
  try {
    const { data, error } = await supabase
      .from('information_schema.columns' as any)
      .select('column_name,data_type,is_nullable,column_default,ordinal_position')
      .eq('table_schema', 'public')
      .eq('table_name', 'email_fraud_logs')
      .order('ordinal_position', { ascending: true })

    if (error) throw error

    const cols = (data as ColumnInfo[]) || []
    return NextResponse.json({ source: 'information_schema', columns: cols })
  } catch (e) {
    // Fallback: infer shape from a sample row in public.email_fraud_logs
    try {
      const { data: sampleRows, error: sampleErr } = await supabase
        .from('email_fraud_logs')
        .select('*')
        .limit(1)

      if (sampleErr) throw sampleErr

      const first = (sampleRows && sampleRows[0]) || null
      const inferred: ColumnInfo[] = first
        ? Object.keys(first).map((k, idx) => ({
            column_name: k,
            data_type: typeof (first as any)[k],
            is_nullable: null,
            column_default: null,
            ordinal_position: idx + 1,
          }))
        : []

      return NextResponse.json({ source: 'inferred', columns: inferred })
    } catch (fallbackErr) {
      return NextResponse.json(
        { error: 'Unable to read schema for email_fraud_logs', details: String(fallbackErr) },
        { status: 500 }
      )
    }
  }
}


