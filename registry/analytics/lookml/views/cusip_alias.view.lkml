view: cusip_alias {
  sql_table_name: ENTERPRISE_DW.CURATED.CURATED_ANALYTICS_CUSIP_ALIAS ;;

  dimension: cusip_alias_pk {
    primary_key: yes
    type: string
    sql: ${TABLE}.cusip_alias_pk ;;
  }

  dimension: asset_fk {
    type: string
    sql: ${TABLE}.asset_fk ;;
  }

  dimension: code {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/CODE"
    sql: ${TABLE}.code ;;
  }

  dimension: identifier {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/IDENTIFIER"
    sql: ${TABLE}.identifier ;;
  }

  dimension: purpose {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP_ALIAS_set/CUSIP_ALIAS_record/PURPOSE"
    sql: ${TABLE}.purpose ;;
  }

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  set: detail { fields: [cusip_alias_pk, asset_fk] }
}
