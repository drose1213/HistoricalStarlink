/**
 * 历史星链探索 - 静态数据
 * MVP版本包含15个核心历史事件
 */

const HISTORY_DATA = {
  events: [
    // ==================== 中国历史 ====================
    {
      id: "shangyang_reform",
      name: "商鞅变法",
      year: -356,
      region: "china",
      importance: 8,
      description: "商鞅在秦孝公支持下进行的系统性变法，推行废井田、重农抑商、奖励军功、建立县制等制度，为秦国统一六国奠定坚实基础。",
      causes: [
        "战国时期诸侯争霸，秦国相对落后",
        "秦孝公求贤若渴",
        "井田制阻碍生产力发展"
      ],
      consequences: [
        "秦国国力大增",
        "建立中央集权制度雏形",
        "为统一六国奠定基础"
      ],
      related: {
        causes: [],
        consequences: [
          { id: "qin_unification", weight: 9 },
          { id: "han_wudi_xiongnu", weight: 6 }
        ]
      }
    },
    {
      id: "qin_unification",
      name: "秦始皇统一六国",
      year: -221,
      region: "china",
      importance: 10,
      description: "秦始皇赢政消灭六国，建立中国历史上第一个大一统王朝，创建皇帝制度，统一文字、度量衡，修筑长城，奠定中国两千余年政治制度基本格局。",
      causes: [
        "商鞅变法国力大增",
        "远交近攻战略成功",
        "六国实力衰退"
      ],
      consequences: [
        "统一文字小篆",
        "统一度量衡",
        "修筑万里长城",
        "建立郡县制"
      ],
      related: {
        causes: [
          { id: "shangyang_reform", weight: 9 },
          { id: "alexander_east", weight: 4 }
        ],
        consequences: [
          { id: "great_wall", weight: 8 },
          { id: "han_empire", weight: 9 }
        ]
      }
    },
    {
      id: "han_empire",
      name: "大汉帝国建立",
      year: -202,
      region: "china",
      importance: 10,
      description: "刘邦击败项羽建立汉朝，实行休养生息政策，文景之治使国力恢复，汉武帝时期开疆拓土，丝绸之路连接东西方，中华文明进入辉煌时代。",
      causes: [
        "秦始皇暴政导致亡国",
        "楚汉争霸项羽失败",
        "分封制向郡县制过渡"
      ],
      consequences: [
        "开启文景之治",
        "汉武帝北击匈奴",
        "丝绸之路开通",
        "儒学成为正统"
      ],
      related: {
        causes: [
          { id: "qin_unification", weight: 8 }
        ],
        consequences: [
          { id: "han_wudi_xiongnu", weight: 9 },
          { id: "silk_road", weight: 8 }
        ]
      }
    },
    {
      id: "han_wudi_xiongnu",
      name: "汉武帝北击匈奴",
      year: -119,
      region: "china",
      importance: 8,
      description: "汉武帝派遣卫青、霍去病率军深入漠北，大破匈奴主力，解除了匈奴对汉朝的威胁，拓地千里，开通丝绸之路，促进了中西交流。",
      causes: [
        "汉朝国力强盛",
        "匈奴频繁入侵边境",
        "卫青霍去病等名将涌现"
      ],
      consequences: [
        "匈奴北撤",
        "西域归附",
        "丝绸之路繁荣"
      ],
      related: {
        causes: [
          { id: "han_empire", weight: 9 },
          { id: "shangyang_reform", weight: 5 }
        ],
        consequences: [
          { id: "silk_road", weight: 8 }
        ]
      }
    },
    {
      id: "tang_sanzang",
      name: "玄奘西行取经",
      year: 629,
      region: "china",
      importance: 7,
      description: "唐代高僧玄奘不畏艰险，西行天竺求取佛经，历时17年，带回佛经657部，促进了佛教在中国的传播，著有《大唐西域记》。",
      causes: [
        "佛教在中国传播需求",
        "国内佛经版本不一",
        "玄奘的宗教热忱"
      ],
      consequences: [
        "佛教在中国广泛传播",
        "中印文化交流加深",
        "《大唐西域记》成书"
      ],
      related: {
        causes: [
          { id: "silk_road", weight: 6 }
        ],
        consequences: [
          { id: "buddhism_china", weight: 9 }
        ]
      }
    },
    {
      id: "ming_foundation",
      name: "明朝建立",
      year: 1368,
      region: "china",
      importance: 9,
      description: "朱元璋推翻元朝统治，建立明朝，实行中央集权，恢复汉族政权，疆域辽阔，郑和下西洋彰显国威，资本主义萌芽出现。",
      causes: [
        "元朝民族压迫严重",
        "农民起义风起云涌",
        "朱元璋军事才能"
      ],
      consequences: [
        "中央集权加强",
        "郑和下西洋",
        "资本主义萌芽"
      ],
      related: {
        causes: [
          { id: "mongol_empire", weight: 8 }
        ],
        consequences: [
          { id: "zhenghe_voyage", weight: 8 },
          { id: "macao's_return", weight: 5 }
        ]
      }
    },
    {
      id: "opium_war",
      name: "鸦片战争",
      year: 1840,
      region: "china",
      importance: 10,
      description: "英国为打开中国市场倾销鸦片，林则徐虎门销烟引发战争，清政府战败签订《南京条约》，中国开始沦为半殖民地半封建社会。",
      causes: [
        "英国工业革命需要市场",
        "贸易逆差导致鸦片贸易",
        "清朝闭关锁国"
      ],
      consequences: [
        "五口通商开放",
        "割让香港",
        "赔款2100万银元",
        "中国社会性质改变"
      ],
      related: {
        causes: [
          { id: "industrial_revolution", weight: 8 },
          { id: "silk_road", weight: 3 }
        ],
        consequences: [
          { id: "xinhai_revolution", weight: 8 }
        ]
      }
    },
    {
      id: "xinhai_revolution",
      name: "辛亥革命",
      year: 1911,
      region: "china",
      importance: 10,
      description: "孙中山领导的民主革命推翻清朝统治，建立中华民国，结束了两千多年的封建帝制，传播了民主共和理念。",
      causes: [
        "列强侵略加深民族危机",
        "洋务运动失败",
        "孙中山革命思想传播",
        "保路运动引发导火索"
      ],
      consequences: [
        "清朝灭亡",
        "建立中华民国",
        "帝制结束",
        "军阀割据混战"
      ],
      related: {
        causes: [
          { id: "opium_war", weight: 7 },
          { id: "french_revolution", weight: 6 }
        ],
        consequences: [
          { id: "wwii_china", weight: 6 }
        ]
      }
    },

    // ==================== 外国历史 ====================
    {
      id: "alexander_east",
      name: "亚历山大东征",
      year: -334,
      region: "foreign",
      importance: 9,
      description: "马其顿国王亚历山大大帝率军东征，征服波斯、埃及、巴比伦等地，建立横跨欧亚非的亚历山大帝国，促进了东西方文化交流。",
      causes: [
        "马其顿军事力量强盛",
        "亚历山大的雄心壮志",
        "波斯帝国内部矛盾"
      ],
      consequences: [
        "希腊化时代开启",
        "文化大交融",
        "丝绸之路西延"
      ],
      related: {
        causes: [],
        consequences: [
          { id: "silk_road", weight: 6 },
          { id: "qin_unification", weight: 4 }
        ]
      }
    },
    {
      id: "rome_empire",
      name: "罗马帝国建立",
      year: -27,
      region: "foreign",
      importance: 10,
      description: "屋大维结束内战，建立罗马帝国，罗马进入鼎盛时期，疆域横跨三大洲，法律、建筑、文化影响深远，至今仍是西方文明的重要基石。",
      causes: [
        "罗马共和国后期内战",
        "屋大维军事胜利",
        "元老院授予奥古斯都称号"
      ],
      consequences: [
        "和平与繁荣的罗马治世",
        "罗马法典编纂",
        "基督教合法化",
        "罗马建筑艺术巅峰"
      ],
      related: {
        causes: [],
        consequences: [
          { id: "christianity_birth", weight: 7 },
          { id: "renaissance", weight: 6 }
        ]
      }
    },
    {
      id: "christianity_birth",
      name: "基督教诞生与传播",
      year: 1,
      region: "foreign",
      importance: 10,
      description: "耶稣在巴勒斯坦地区创立基督教，强调博爱、救赎与原罪，影响了整个西方世界的价值观体系，罗马帝国后期将其定为国教。",
      causes: [
        "罗马帝国统治下民不聊生",
        "犹太教一神信仰传统",
        "人们对救赎的渴望"
      ],
      consequences: [
        "成为罗马国教",
        "中世纪欧洲精神支柱",
        "影响法律和政治制度",
        "塑造西方价值观"
      ],
      related: {
        causes: [
          { id: "rome_empire", weight: 7 }
        ],
        consequences: [
          { id: "crusades", weight: 8 },
          { id: "enlightenment", weight: 6 }
        ]
      }
    },
    {
      id: "renaissance",
      name: "文艺复兴",
      year: 1492,
      region: "foreign",
      importance: 10,
      description: "以意大利为中心的思想文化运动，强调人文主义，提倡以人为中心，肯定人的价值和尊严，是欧洲从中世纪向近代过渡的重要转折点。",
      causes: [
        "意大利城市经济繁荣",
        "古希腊罗马典籍回归",
        "教会需要新艺术形式",
        "印刷术传播知识"
      ],
      consequences: [
        "人文主义思想兴起",
        "科学革命萌芽",
        "艺术创作高峰",
        "宗教改革酝酿"
      ],
      related: {
        causes: [
          { id: "rome_empire", weight: 7 }
        ],
        consequences: [
          { id: "enlightenment", weight: 8 },
          { id: "industrial_revolution", weight: 6 }
        ]
      }
    },
    {
      id: "crusades",
      name: "十字军东征",
      year: 1096,
      region: "foreign",
      importance: 8,
      description: "西欧封建主和教会以收复圣地为名发动的一系列军事远征，持续近两百年，虽然军事目标失败，但客观上促进了东西方文化交流。",
      causes: [
        "基督教传播与圣地情结",
        "欧洲人口增长与扩张需求",
        "教皇权威与军事号召"
      ],
      consequences: [
        "东西方文化交流加速",
        "拜占庭帝国衰弱",
        "伊斯兰世界分裂",
        "骑士制度发展"
      ],
      related: {
        causes: [
          { id: "christianity_birth", weight: 8 }
        ],
        consequences: [
          { id: "renaissance", weight: 5 }
        ]
      }
    },
    {
      id: "silk_road",
      name: "丝绸之路繁荣",
      year: -100,
      region: "foreign",
      importance: 8,
      description: "连接东西方的商路网络，运送丝绸、香料、玻璃等商品，促进了欧亚大陆间的经济文化交流，驼铃声中见证了无数文明的兴衰。",
      causes: [
        "汉朝与罗马帝国需求",
        "张骞出使西域",
        "亚历山大东征影响"
      ],
      consequences: [
        "东西方物种交流",
        "佛教传入中国",
        "罗马奢侈品热潮",
        "贸易城市兴起"
      ],
      related: {
        causes: [
          { id: "han_empire", weight: 8 },
          { id: "alexander_east", weight: 6 }
        ],
        consequences: [
          { id: "tang_sanzang", weight: 7 },
          { id: "mongol_empire", weight: 6 }
        ]
      }
    },
    {
      id: "mongol_empire",
      name: "蒙古帝国崛起",
      year: 1206,
      region: "foreign",
      importance: 9,
      description: "成吉思汗统一蒙古各部后发动大规模征服战争，建立人类历史上最大连续版图的帝国，创造了世界上最强大的军事力量。",
      causes: [
        "蒙古草原统一",
        "成吉思汗军事天才",
        "骑兵战术创新"
      ],
      consequences: [
        "丝绸之路再次统一",
        "东西方交流频繁",
        "元朝建立",
        "欧洲恐惧\"黄祸\""
      ],
      related: {
        causes: [
          { id: "silk_road", weight: 6 }
        ],
        consequences: [
          { id: "ming_foundation", weight: 8 },
          { id: "renaissance", weight: 4 }
        ]
      }
    },
    {
      id: "enlightenment",
      name: "启蒙运动",
      year: 1687,
      region: "foreign",
      importance: 9,
      description: "以理性为核心的思想解放运动，伏尔泰、卢梭、孟德斯鸠等思想家倡导自由、平等、民主，为法国大革命和美国独立奠定思想基础。",
      causes: [
        "文艺复兴思想积累",
        "科学革命冲击神学",
        "印刷术普及思想",
        "君主专制弊端显现"
      ],
      consequences: [
        "法国大革命爆发",
        "美国独立宣言",
        "民主制度建立",
        "科学精神传播"
      ],
      related: {
        causes: [
          { id: "renaissance", weight: 8 },
          { id: "christianity_birth", weight: 5 }
        ],
        consequences: [
          { id: "french_revolution", weight: 9 },
          { id: "american_independence", weight: 8 }
        ]
      }
    },
    {
      id: "french_revolution",
      name: "法国大革命",
      year: 1789,
      region: "foreign",
      importance: 10,
      description: "巴黎人民攻占巴士底狱，自由、平等、博爱的口号响彻欧洲，推翻封建专制，传播民主共和理念，深刻影响19世纪世界历史进程。",
      causes: [
        "启蒙思想传播",
        "财政危机与社会不公",
        "美国独立示范效应",
        "三级会议召开"
      ],
      consequences: [
        "封建制度崩溃",
        "拿破仑崛起",
        "民族主义兴起",
        "《人权宣言》诞生"
      ],
      related: {
        causes: [
          { id: "enlightenment", weight: 9 }
        ],
        consequences: [
          { id: "napoleon", weight: 9 },
          { id: "xinhai_revolution", weight: 6 }
        ]
      }
    },
    {
      id: "industrial_revolution",
      name: "工业革命",
      year: 1760,
      region: "foreign",
      importance: 10,
      description: "从英国开始的机器生产取代手工劳动的变革，蒸汽机、纺织机的发明改变了生产方式，人类进入工业社会，生产力空前提高。",
      causes: [
        "圈地运动提供劳动力",
        "殖民扩张带来原料",
        "手工技艺积累",
        "市场需求扩大"
      ],
      consequences: [
        "工厂制度建立",
        "城市化进程加速",
        "工人阶级形成",
        "帝国主义扩张"
      ],
      related: {
        causes: [
          { id: "renaissance", weight: 6 }
        ],
        consequences: [
          { id: "opium_war", weight: 8 },
          { id: "american_independence", weight: 5 }
        ]
      }
    },
    {
      id: "american_independence",
      name: "美国独立",
      year: 1776,
      region: "foreign",
      importance: 9,
      description: "北美十三州发表《独立宣言》，宣布脱离英国独立，建立联邦制共和国，\"人人生而平等\"的理念影响深远，为后世民主运动提供范本。",
      causes: [
        "启蒙思想影响",
        "英国高压统治",
        "列克星敦枪声",
        "华盛顿领导才能"
      ],
      consequences: [
        "三权分立制度建立",
        "民主共和理念传播",
        "法国大革命助推",
        "西进运动开始"
      ],
      related: {
        causes: [
          { id: "enlightenment", weight: 8 },
          { id: "industrial_revolution", weight: 5 }
        ],
        consequences: [
          { id: "french_revolution", weight: 7 },
          { id: "xinhai_revolution", weight: 5 }
        ]
      }
    },
    {
      id: "napoleon",
      name: "拿破仑时代",
      year: 1804,
      region: "foreign",
      importance: 8,
      description: "拿破仑通过军事才能登上权力巅峰，建立法兰西第一帝国，颁布《拿破仑法典》，横扫欧洲封建势力，虽最终失败但深刻改变了欧洲格局。",
      causes: [
        "法国大革命后局势动荡",
        "拿破仑军事天才",
        "民众渴望稳定"
      ],
      consequences: [
        "《拿破仑法典》流传",
        "民族主义觉醒",
        "维也纳体系建立",
        "欧洲均势格局"
      ],
      related: {
        causes: [
          { id: "french_revolution", weight: 9 }
        ],
        consequences: [
          { id: "enlightenment", weight: 4 }
        ]
      }
    },
    {
      id: "wwii_china",
      name: "中国抗日战争",
      year: 1937,
      region: "china",
      importance: 10,
      description: "日本全面侵华，中国人民进行艰苦卓绝的八年抗战，最终取得胜利，是中华民族由衰败走向振兴的重大转折点。",
      causes: [
        "日本军国主义扩张",
        "九一八事变后侵占东北",
        "华北事变危机",
        "国共第二次合作"
      ],
      consequences: [
        "日本无条件投降",
        "新中国成立条件",
        "联合国常任理事国地位",
        "中华民族觉醒"
      ],
      related: {
        causes: [
          { id: "opium_war", weight: 6 },
          { id: "xinhai_revolution", weight: 5 }
        ],
        consequences: [
          { id: "macao's_return", weight: 7 }
        ]
      }
    },
    {
      id: "great_wall",
      name: "万里长城修建",
      year: -221,
      region: "china",
      importance: 7,
      description: "秦始皇统一六国后连接和修缮北方长城，抵御匈奴入侵，成为中国古代最伟大的军事防御工程，也是中华民族的精神象征。",
      causes: [
        "北方匈奴威胁",
        "统一后有能力调动资源",
        "军事防御需求"
      ],
      consequences: [
        "北方边境安全",
        "中华文明屏障",
        "民族精神象征"
      ],
      related: {
        causes: [
          { id: "qin_unification", weight: 9 }
        ],
        consequences: []
      }
    },
    {
      id: "buddhism_china",
      name: "佛教中国化",
      year: 700,
      region: "china",
      importance: 8,
      description: "佛教从印度传入中国后，与儒家、道教融合，形成禅宗、净土宗等中国特色佛教流派，成为中国三大宗教之一，深刻影响文化、艺术、生活。",
      causes: [
        "玄奘取经传播",
        "丝绸之路传入",
        "统治者支持"
      ],
      consequences: [
        "佛塔寺庙遍布",
        "石窟艺术兴起",
        "宋明理学融合",
        "向外传播至日本朝鲜"
      ],
      related: {
        causes: [
          { id: "tang_sanzang", weight: 9 },
          { id: "silk_road", weight: 7 }
        ],
        consequences: []
      }
    },
    {
      id: "zhenghe_voyage",
      name: "郑和下西洋",
      year: 1405,
      region: "china",
      importance: 8,
      description: "明代郑和率庞大船队七下西洋，远达非洲东海岸，展示大明国威，促进了中外贸易与文化交流，是中国航海史上的壮举。",
      causes: [
        "明朝国力强盛",
        "朱棣宣扬国威",
        "寻找建文帝下落"
      ],
      consequences: [
        "中外贸易繁荣",
        "华人移居南洋",
        "海禁政策后终止",
        "航海技术外传"
      ],
      related: {
        causes: [
          { id: "ming_foundation", weight: 8 }
        ],
        consequences: [
          { id: "opium_war", weight: 4 }
        ]
      }
    },
    {
      id: "macao's_return",
      name: "澳门回归",
      year: 1999,
      region: "china",
      importance: 8,
      description: "澳门特别行政区成立，结束葡萄牙殖民统治，中国政府恢复对澳门行使主权，标志着祖国统一大业迈出重要一步。",
      causes: [
        "改革开放后国力增强",
        "一国两制政策成功",
        "香港回归示范效应"
      ],
      consequences: [
        "一国两制成功实践",
        "葡人治澳延续",
        "澳门经济转型",
        "台海和平统一希望"
      ],
      related: {
        causes: [
          { id: "ming_foundation", weight: 4 },
          { id: "wwii_china", weight: 5 }
        ],
        consequences: []
      }
    }
  ],

  // 补充更多关联关系
  additionalRelations: {
    silk_road: { causes: [{ id: "alexander_east", weight: 5 }], consequences: [] },
    mongol_empire: { causes: [], consequences: [{ id: "renaissance", weight: 3 }] }
  }
};

// 数据查找工具函数
const DataUtils = {
  // 根据ID获取事件
  getEventById(id) {
    return HISTORY_DATA.events.find(e => e.id === id);
  },

  // 按区域筛选
  filterByRegion(region) {
    if (region === 'all') return HISTORY_DATA.events;
    return HISTORY_DATA.events.filter(e => e.region === region);
  },

  // 获取关联事件
  getRelatedEvents(eventId, type = 'all') {
    const event = this.getEventById(eventId);
    if (!event) return { causes: [], consequences: [] };

    const result = { causes: [], consequences: [] };

    if (type === 'all' || type === 'causes') {
      event.related.causes.forEach(rel => {
        const relatedEvent = this.getEventById(rel.id);
        if (relatedEvent) {
          result.causes.push({ ...relatedEvent, weight: rel.weight });
        }
      });
    }

    if (type === 'all' || type === 'consequences') {
      event.related.consequences.forEach(rel => {
        const relatedEvent = this.getEventById(rel.id);
        if (relatedEvent) {
          result.consequences.push({ ...relatedEvent, weight: rel.weight });
        }
      });
    }

    // 排序：按重要性降序，最多10个
    result.causes.sort((a, b) => b.importance - a.importance).slice(0, 5);
    result.consequences.sort((a, b) => b.importance - a.importance).slice(0, 5);

    return result;
  },

  // 获取时间范围
  getYearRange() {
    const years = HISTORY_DATA.events.map(e => e.year);
    return {
      min: Math.min(...years),
      max: Math.max(...years)
    };
  }
};

// 导出
if (typeof module !== 'undefined' && module.exports) {
  module.exports = { HISTORY_DATA, DataUtils };
}
