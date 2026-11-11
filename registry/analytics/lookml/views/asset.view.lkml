view: asset {
  sql_table_name: ENTERPRISE_DW.CURATED.CURATED_ANALYTICS_ASSET ;;

  dimension: asset_pk {
    primary_key: yes
    type: string
    sql: ${TABLE}.asset_pk ;;
  }

  dimension: assets_fk {
    type: string
    sql: ${TABLE}.assets_fk ;;
  }

  dimension: class_val {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CLASS"
    sql: ${TABLE}.class_val ;;
  }

  dimension: accrual_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/ACCRUAL_DT"
    sql: ${TABLE}.accrual_dt ;;
  }

  dimension: amt_isu {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/AMT_ISU"
    sql: ${TABLE}.amt_isu ;;
  }

  dimension: announce_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/ANNOUNCE_DT"
    sql: ${TABLE}.announce_dt ;;
  }

  dimension: calc_type {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/CALC_TYPE"
    sql: ${TABLE}.calc_type ;;
  }

  dimension: call_mandatory {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CALL_MANDATORY"
    sql: ${TABLE}.call_mandatory ;;
  }

  dimension: call_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CALL_TYPE"
    sql: ${TABLE}.call_type ;;
  }

  dimension: cd_instmt_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CD_INSTMT_TYPE"
    sql: ${TABLE}.cd_instmt_type ;;
  }

  dimension: change_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CHANGE_DT"
    sql: ${TABLE}.change_dt ;;
  }

  dimension: compound_flag {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/COMPOUND_FLAG"
    sql: ${TABLE}.compound_flag ;;
  }

  dimension: country {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUNTRY"
    sql: ${TABLE}.country ;;
  }

  dimension: coupon_fix {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUPON_FIX"
    sql: ${TABLE}.coupon_fix ;;
  }

  dimension: coup_freq {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/COUP_FREQ"
    sql: ${TABLE}.coup_freq ;;
  }

  dimension: cpn_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CPN_TYPE"
    sql: ${TABLE}.cpn_type ;;
  }

  dimension: currency {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CURRENCY"
    sql: ${TABLE}.currency ;;
  }

  dimension: cusip {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP"
    sql: ${TABLE}.cusip ;;
  }

  dimension: cusip_type {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/CUSIP_TYPE"
    sql: ${TABLE}.cusip_type ;;
  }

  dimension: date_conv {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/DATE_CONV"
    sql: ${TABLE}.date_conv ;;
  }

  dimension: desc_instmt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/DESC_INSTMT"
    sql: ${TABLE}.desc_instmt ;;
  }

  dimension: end_adj_flag {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/END_ADJ_FLAG"
    sql: ${TABLE}.end_adj_flag ;;
  }

  dimension: first_pay_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/FIRST_PAY_DT"
    sql: ${TABLE}.first_pay_dt ;;
  }

  dimension: first_settle_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/FIRST_SETTLE_DT"
    sql: ${TABLE}.first_settle_dt ;;
  }

  dimension: flag_144_a {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/FLAG_144A"
    sql: ${TABLE}.flag_144_a ;;
  }

  dimension: flag_reg_s {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/FLAG_REG_S"
    sql: ${TABLE}.flag_reg_s ;;
  }

  dimension: issue_price {
    type: number
    description: "XPath: /ASSETS/ASSET/BND_CORP/ISSUE_PRICE"
    sql: ${TABLE}.issue_price ;;
  }

  dimension: maturity_dt {
    type: string
    description: "XPath: /ASSETS/ASSET/BND_CORP/MATURITY_DT"
    sql: ${TABLE}.maturity_dt ;;
  }

  measure: count {
    type: count
    drill_fields: [detail*]
  }

  set: detail { fields: [asset_pk, assets_fk] }
}
