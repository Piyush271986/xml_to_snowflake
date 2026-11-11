view: cusip2 {
  sql_table_name: ENTERPRISE_DW.CURATED.CURATED_ANALYTICS_CUSIP2 ;;

  dimension: cusip2_pk {
    primary_key: yes
    type: string
    sql: ${TABLE}.cusip2_pk ;;
  }

  dimension: asset_fk {
    type: string
    sql: ${TABLE}.asset_fk ;;
  }

  dimension: code {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record/CODE"
    sql: ${TABLE}.code ;;
  }

  dimension: identifier {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP2_set/CUSIP2_record/IDENTIFIER"
    sql: ${TABLE}.identifier ;;
  }

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  set: detail { fields: [cusip2_pk, asset_fk] }
}
