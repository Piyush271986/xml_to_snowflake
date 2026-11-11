view: assets {
  sql_table_name: ENTERPRISE_DW.CURATED.CURATED_ANALYTICS ;;

  dimension: assets_pk {
    primary_key: yes
    type: string
    sql: ${TABLE}.assets_pk ;;
  }

  dimension: asof_date {
    type: string
    description: "XPath: /ASSETS/@ASOF_DATE"
    sql: ${TABLE}.asof_date ;;
  }

  dimension: create_date {
    type: string
    description: "XPath: /ASSETS/@CREATE_DATE"
    sql: ${TABLE}.create_date ;;
  }

  dimension: records {
    type: number
    description: "XPath: /ASSETS/@RECORDS"
    sql: ${TABLE}.records ;;
  }

  dimension: esg_rating {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/ESG_RATING"
    sql: ${TABLE}.esg_rating ;;
  }

  dimension: rating_agency {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/RATING_AGENCY"
    sql: ${TABLE}.rating_agency ;;
  }

  dimension: seniority_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/SENIORITY_TYPE"
    sql: ${TABLE}.seniority_type ;;
  }

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  set: detail { fields: [assets_pk] }
}
