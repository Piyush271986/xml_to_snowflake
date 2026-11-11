view: country_classification {
  sql_table_name: ENTERPRISE_DW.CURATED.CURATED_ANALYTICS_COUNTRY_CLASSIFICATION ;;

  dimension: country_classification_pk {
    primary_key: yes
    type: string
    sql: ${TABLE}.country_classification_pk ;;
  }

  dimension: asset_fk {
    type: string
    sql: ${TABLE}.asset_fk ;;
  }

  dimension: cntry {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY"
    sql: ${TABLE}.cntry ;;
  }

  dimension: cntry_src {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY_SRC"
    sql: ${TABLE}.cntry_src ;;
  }

  dimension: cntry_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUNTRY_CLASSIFICATION_set/COUNTRY_CLASSIFICATION_record/CNTRY_TYPE"
    sql: ${TABLE}.cntry_type ;;
  }

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  set: detail { fields: [country_classification_pk, asset_fk] }
}
