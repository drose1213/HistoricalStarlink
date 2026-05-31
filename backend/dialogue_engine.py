"""
对话引擎 - 预置剧本实现的对话式历史探索
不依赖LLM，使用预置的多轮对话剧本和关键词匹配
"""
import uuid
import re
from typing import Optional


DIALOGUE_SCRIPTS = {
    "qin_unification": {
        "npc_name": "赢政",
        "npc_role": "秦王",
        "npc_symbol": "☰",
        "opening": "……你是何人？竟能穿越时空来到寡人的面前。寡人刚刚灭了六国，天下初定，你从何处而来？",
        "context": "公元前221年，秦王赢政刚刚统一六国，自称始皇帝。他正在考虑如何治理这个庞大的帝国。",
        "rounds": [
            {
                "round": 1,
                "narrative": "秦始皇端坐在咸阳宫的龙椅之上，目光如炬地看着你。\n\n「寡人听闻后世之人对朕多有非议，你既来自未来，且说说看——朕统一六国，是功是过？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "陛下统一六国，结束数百年战乱，功在千秋！",
                        "consequence": "始皇帝龙颜大悦",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "统一虽好，但焚书坑儒恐损天下文脉。",
                        "consequence": "始皇帝面色微沉",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "陛下可曾想过，帝国能否千秋万代？",
                        "consequence": "始皇帝陷入沉思",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "秦始皇抚掌大笑：「说得好！天下苦战久矣，只有朕能终结这场乱世。朕已下令统一文字、度量衡，修筑长城抵御匈奴。这些功业，后世之人应当铭记！」",
                "narrative_disagree": "秦始皇冷冷道：「焚书？那些腐儒以古非今，蛊惑人心。若不以法治国，天下必将再度分裂。你可知道，六国的史书上写了多少诋毁秦国的话？」",
                "narrative_thoughtful": "秦始皇沉默片刻，说道：「千秋万代……朕已命人寻觅长生不老之药。但你说得对，朕需要为后世留下制度，而非仅仅依赖朕一人。」",
                "narrative_default": "秦始皇沉声道：「你的话倒有几分道理。朕且问你，若你能改变朕的一道旨意，你会改变什么？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "请陛下善待儒生，以德治国与法治并行。",
                        "consequence": "秦始皇犹豫片刻，似乎有所触动",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "请陛下早立太子，稳固继承之制。",
                        "consequence": "始皇帝眉头紧锁",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "陛下不必改变什么，历史自有其轨迹。",
                        "consequence": "始皇帝似乎有些失望",
                        "timeline_change": False,
                        "next_round": 3,
                        "mood": "disagree"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "秦始皇站起身来，望着殿外的星空：「你说的……朕会考虑。也许，朕可以给那些儒生一个机会。但若他们再敢以古非今，朕绝不姑息。」\n\n忽然，时空开始扭曲，你的身影渐渐模糊……",
                "narrative_disagree": "秦始皇站起身来，声音低沉：「扶苏……他太过仁慈，不适合做帝王。但你说得对，朕需要一个更稳妥的继承方案。」\n\n时空开始扭曲，你感受到一股强大的力量正在将你拉回未来……",
                "narrative_default": "秦始皇最后看了你一眼：「也许，这就是天意。朕的帝国，自有其命运。」\n\n时空的裂缝渐渐闭合，你回到了属于自己的时代……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】秦始皇统一六国后推行严刑峻法，焚书坑儒以统一思想。其子胡亥继位后暴政连连，秦朝二世而亡。但统一文字、度量衡、郡县制等制度影响中国两千余年。",
            "altered": "【平行时间线】在你的建议下，秦始皇放缓了对儒生的迫害，允许部分学派保留。秦朝的统治因此获得了更多知识分子的支持，帝国延续了更长时间。历史的河流在此分岔……"
        }
    },

    "roman_empire": {
        "npc_name": "屋大维",
        "npc_role": "罗马皇帝奥古斯都",
        "npc_symbol": "♔",
        "opening": "陌生人，你是谁？卫兵为何放你进入我的宫殿？……等等，你的眼神不属于这个时代。你是从未来来的？",
        "context": "公元前27年，屋大维刚刚获得了'奥古斯都'的称号，建立了罗马帝国。罗马从共和国走向帝制，正处于历史的转折点。",
        "rounds": [
            {
                "round": 1,
                "narrative": "奥古斯都坐在大理石宝座上，身后是描绘罗马军团凯旋的壁画。他审视着你，眼中带着好奇与戒备。\n\n「你来自未来？那么告诉我，后世如何评价我——是暴君，还是明君？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "陛下建立了长达两百年的'罗马和平'，是伟大的统治者。",
                        "consequence": "奥古斯都露出满意的微笑",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "您摧毁了共和制度，虽带来和平，却也埋下了隐患。",
                        "consequence": "奥古斯都表情变得严肃",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "后世有位叫凯撒的人，也走上了和您相似的道路……",
                        "consequence": "奥古斯都陷入回忆",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "奥古斯都站起身来，走到一幅巨大的罗马帝国地图前：「两百年？很好。朕建立帝国不是为了个人荣耀，而是因为共和国已经腐朽。元老院的权力斗争让罗马流了太多血。」",
                "narrative_disagree": "奥古斯都冷哼一声：「共和？你见过共和国末期的样子吗？苏拉和马略的内战、凯撒被刺杀……共和制度已经名存实亡。朕用帝制换来了和平，这是唯一的出路。」",
                "narrative_thoughtful": "奥古斯都叹了口气：「凯撒……他是我的养父，也是罗马最伟大的将军。但他太骄傲了，以为自己可以凌驾于一切之上。朕从他的死中学到了——权力需要伪装。」",
                "narrative_default": "奥古斯都目光深邃地看着你：「你的话让朕思考了很多。朕再问你——如果你能改变罗马的一件事，你会改变什么？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "请建立明确的继承制度，避免后世的帝位之争。",
                        "consequence": "奥古斯都若有所思",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "请善待行省人民，不要过度扩张疆域。",
                        "consequence": "奥古斯都面露犹豫",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "陛下已经做得够好了，历史自有其发展规律。",
                        "consequence": "奥古斯都微微颔首",
                        "timeline_change": False,
                        "next_round": 3,
                        "mood": "agree"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "奥古斯都沉思良久：「你说得对……提比略虽然能干，但性情冷酷。也许朕应该为帝国留下一套更完善的继承制度。」\n\n时空开始扭曲，罗马宫殿的影像渐渐模糊……",
                "narrative_disagree": "奥古斯都望向远方：「行省的人民……是啊，帝国太大了，总有一天会超出我们的控制。但至少现在，朕要确保罗马的边界安全。」\n\n时光的洪流将你卷走，罗马渐渐远去……",
                "narrative_default": "奥古斯都最后说道：「无论如何，朕会继续为罗马而战。历史的车轮不会因一个人而停下。」\n\n你感到时间线正在愈合，回到了属于你的时代……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】奥古斯都建立了元首制，开创了罗马帝国两百年的'罗马和平'。但他未能解决继承问题，后世皇帝更替频繁，帝国最终在公元476年灭亡。",
            "altered": "【平行时间线】奥古斯都建立了正式的继承制度，罗马帝国的权力交接变得有序。帝国延续了更长的时间，东西罗马的分裂或许可以避免……"
        }
    },

    "french_revolution": {
        "npc_name": "一位巴黎市民",
        "npc_role": "革命参与者",
        "npc_symbol": "⚔",
        "opening": "公民！你也来参加革命了吗？巴士底狱已经被攻下了！自由、平等、博爱——这才是我们应该拥有的权利！",
        "context": "1789年7月14日，巴黎人民攻占巴士底狱，法国大革命爆发。整个法国正处在翻天覆地的变革之中。",
        "rounds": [
            {
                "round": 1,
                "narrative": "巴黎的街道上弥漫着硝烟和热血的气息。一位戴着红白蓝三色帽章的市民兴奋地抓住你的手。\n\n「公民，你来得正好！路易十六那个暴君终于要倒台了！但革命需要每一个人的力量——你愿意和我们一起战斗吗？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "我支持革命！人民有权利推翻暴政！",
                        "consequence": "市民激动地拥抱了你",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "暴力革命会带来更多的暴力，你们确定要走这条路吗？",
                        "consequence": "市民的表情变得警惕",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "我见过未来的法国……事情可能会走向极端。",
                        "consequence": "市民困惑地看着你",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "市民举起三色旗高呼：「说得好！我们要建立一个人人平等的新法兰西！但……最近有些激进派在谈论'断头台'，你对这事怎么看？」",
                "narrative_disagree": "市民皱起眉头：「你不明白吗？贵族和国王骑在我们头上几百年了！不流血怎么能换来自由？但你说得也有道理……我听说罗伯斯庇尔越来越极端了。」",
                "narrative_thoughtful": "市民压低声音：「未来的法国……你是说革命会失控？我也有些担心。雅各宾派的那些人越来越激进了。你知道'断头台'吗？」",
                "narrative_default": "市民沉吟片刻：「你说的也有道理。那么，你觉得我们应该怎样做，才能既实现革命的目标，又不让它变成一场灾难？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "阻止激进派，让革命保持理性和秩序。",
                        "consequence": "市民似乎被说服了",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "让人民的意志自由表达，即使这意味着更多的冲突。",
                        "consequence": "市民犹豫不决",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "为革命的领袖们设置权力限制，防止独裁。",
                        "consequence": "市民若有所思",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "市民点头说道：「你说得对。革命不应该变成新的暴政。但愿我们的选择能改变什么……」\n\n远处传来炮声，时空开始扭曲，巴黎的街道渐渐模糊……",
                "narrative_disagree": "市民握紧拳头：「也许你是对的。但如果不去争取，我们永远只是奴隶！」\n\n革命的火焰在你眼前燃烧，时间线开始扭曲……",
                "narrative_default": "市民最后望向天空：「无论怎样，今天的巴黎永远不会忘记。自由的代价，我们必须承受。」\n\n你感到一阵眩晕，时间的洪流将你带走了……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】法国大革命推翻了封建专制，传播了民主共和理念。但随后的雅各宾专政和恐怖统治导致数万人被送上断头台，最终拿破仑上台，法国陷入新的独裁。",
            "altered": "【平行时间线】在你的干预下，激进派被有效制约。法国大革命以更温和的方式推进，君主立宪制得以保留，欧洲避免了此后数十年的战争动荡。但这只是另一个平行宇宙的故事……"
        }
    },

    "shangyang_reform": {
        "npc_name": "商鞅",
        "npc_role": "秦国变法者",
        "npc_symbol": "⚖",
        "opening": "阁下是谁？竟能越过军营守卫来到此处。你的眼神……不属于这个年代。说吧，你从何处来？",
        "context": "公元前356年，商鞅在秦孝公的支持下开始推行变法，废井田、重农抑商、奖励军功。整个秦国正处在翻天覆地的变革之中。",
        "rounds": [
            {
                "round": 1,
                "narrative": "商鞅端坐在案前，面前铺满了竹简。烛火映照着他坚毅的面容。\n\n「变法已推行数月，旧贵族恨我入骨，但秦国的国力正在迅速增强。你既从未来而来——告诉我，后世如何评价我的变法？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "先生的变法使秦国从弱变强，为统一六国奠定了基础！",
                        "consequence": "商鞅露出欣慰的神色",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "变法虽强，但法律过于严苛，百姓苦不堪言。",
                        "consequence": "商鞅眉头紧锁",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "先生可曾想过，变法成功之后，自己会是什么下场？",
                        "consequence": "商鞅神色微变",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "商鞅放下竹简，目光坚定：「秦国积弱百年，非铁腕不能治。废井田、奖军功，每一项法令都是为了让秦国强大。我已做好了被旧势力报复的准备。」",
                "narrative_disagree": "商鞅站起身来，声音洪亮：「严苛？乱世用重典！若不以法治国，秦国将永远是西陲弱国。百姓眼前的苦难，换来的是百年后的太平！」",
                "narrative_thoughtful": "商鞅沉默良久，缓缓说道：「我的下场……我早已预见。新法触动了太多权贵的利益。但法之不行，自上犯之——我若退缩，变法将前功尽弃。」",
                "narrative_default": "商鞅看着你：「你的话倒有几分见地。如果你能给变法一个建议，你会说什么？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "建议在严法之外，增加教化百姓的措施。",
                        "consequence": "商鞅若有所思",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "请培养更多支持变法的人才，确保变法延续。",
                        "consequence": "商鞅点头",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "先生已做得很好，历史自有其走向。",
                        "consequence": "商鞅微微叹息",
                        "timeline_change": False,
                        "next_round": 3,
                        "mood": "agree"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "商鞅站起身来，望着帐外的星空：「教化……你说得对。法能治身，但不能治心。也许，我应该在变法中加入更多教化的内容。」\n\n时空开始扭曲，烛火渐渐模糊……",
                "narrative_disagree": "商鞅点头道：「人才……公孙衍、司马错，他们都是变法培养出来的人才。但一个人的力量终究有限。我需要让更多人理解变法的意义。」\n\n时空开始扭曲，竹简上的文字渐渐散去……",
                "narrative_default": "商鞅最后说道：「无论后世如何评价我，我都不后悔。为了秦国的强大，我愿意付出一切代价。」\n\n你感到时空在愈合，回到了属于你的时代……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】商鞅变法使秦国迅速强大，为统一六国奠定基础。但变法也触动了旧贵族利益，秦孝公死后商鞅被车裂。然而，他的制度被秦国沿用，最终成就了秦始皇的霸业。",
            "altered": "【平行时间线】商鞅在你的建议下增加了教化措施，使变法获得了更多百姓的支持。秦国的崛起更加平稳，变法者的命运也不再那么悲惨……"
        }
    },

    "han_empire": {
        "npc_name": "刘邦",
        "npc_role": "汉高祖",
        "npc_symbol": "龙",
        "opening": "你是什么人？竟然能闯入朕的宫殿！……等等，你的眼神不对劲。你不是这个时代的人吧？",
        "context": "公元前202年，刘邦击败项羽，建立大汉帝国。他正在思考如何治理这个新生的帝国。",
        "rounds": [
            {
                "round": 1,
                "narrative": "刘邦坐在龙椅上，虽然出身布衣，但眉宇间已有了帝王之气。他好奇地打量着你。\n\n「你是从未来来的？有意思！那朕问你——大汉能传多少世？后人怎么评价朕？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "大汉延续四百年，陛下开创了辉煌的汉朝！",
                        "consequence": "刘邦龙颜大悦",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "陛下虽善用人，但治国理政似乎不如打仗。",
                        "consequence": "刘邦面色微变",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "陛下可曾担心，异姓王们会威胁皇权？",
                        "consequence": "刘邦眼神变得锐利",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "刘邦哈哈大笑：「四百年！好！朕就知道，跟着朕打天下的兄弟们没有白忙活！来来来，跟朕说说，四百年里有什么大事？」",
                "narrative_disagree": "刘邦不以为然地摆摆手：「朕出身布衣，能打下这江山靠的是识人用人。治国嘛……有萧何、张良在，朕怕什么？」",
                "narrative_thoughtful": "刘邦眼神一凛：「异姓王……韩信、彭越、英布，他们确实让朕寝食难安。你有什么好办法？」",
                "narrative_default": "刘邦摆出一副虚心请教的样子：「你是从未来来的人，见识肯定比朕广。你觉得朕该怎么做？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "请善待功臣，不要兔死狗烹。",
                        "consequence": "刘邦沉默了",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "请推行休养生息政策，让百姓安居乐业。",
                        "consequence": "刘邦若有所思",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "陛下顺其自然就好，历史自有安排。",
                        "consequence": "刘邦耸了耸肩",
                        "timeline_change": False,
                        "next_round": 3,
                        "mood": "agree"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "刘邦叹了口气：「兔死狗烹……你说得对，韩信他们为朕打下了江山，朕不应该亏待他们。但皇权的事，容朕再想想。」\n\n时空开始扭曲，宫殿的影像渐渐模糊……",
                "narrative_disagree": "刘邦点头道：「休养生息！萧何也是这么说的。好，朕听你们的，让百姓好好歇歇。」\n\n时空开始扭曲，刘邦的身影渐渐远去……",
                "narrative_default": "刘邦最后笑着说：「不管怎样，朕这辈子从一个亭长做到皇帝，够本了！后世的事，就交给后世吧。」\n\n你感到时间的洪流将你带走……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】刘邦建立汉朝后大杀功臣，韩信、彭越、英布等异姓王先后被诛。但'休养生息'政策使国力恢复，'文景之治'奠定了汉朝四百年的基业。",
            "altered": "【平行时间线】刘邦在你的建议下善待功臣，建立了更稳固的君臣关系。汉朝的开国功臣们得以善终，帝国的根基更加牢固……"
        }
    },

    "alexander_east": {
        "npc_name": "亚历山大",
        "npc_role": "马其顿国王",
        "npc_symbol": "⚔",
        "opening": "Who are you? You don't look like one of my soldiers... nor a Persian spy. Something about your appearance is strange. Speak — who sent you?",
        "context": "334 BC. Alexander the Great has just begun his legendary campaign eastward from Greece. He has defeated the Persians at Granicus and is pushing deeper into Asia.",
        "rounds": [
            {
                "round": 1,
                "narrative": "亚历山大身披战甲，坐在营帐中的王座上。他的眼神锐利如鹰，身后挂着从波斯人那里缴获的地图。\n\n「你说你来自未来？那告诉我——我的帝国能维持多久？我最终能打到哪里？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "陛下建立了一个横跨欧亚非的大帝国，但英年早逝。",
                        "consequence": "亚历山大沉默了一瞬",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "陛下是历史上最伟大的征服者，后人称您为'大帝'。",
                        "consequence": "亚历山大露出骄傲的微笑",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "c",
                        "text": "征服虽然伟大，但无数人为此付出了生命。",
                        "consequence": "亚历山大表情变得凝重",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_thoughtful": "亚历山大站起身来，走到帐篷口望着远方：「英年早逝……我一直在想，时间是不是我最大的敌人。我还有太多地方没有征服，太多梦想没有实现。」",
                "narrative_agree": "亚历山大拍了拍手中的佩剑：「大帝？我喜欢这个称号。但我征服的不是为了名号——我是为了追寻荷马史诗中阿喀琉斯的荣光！」",
                "narrative_disagree": "亚历山大皱起眉头：「生命？战争总是要流血的。但我的征服不仅仅是杀戮——我要把希腊文明带到世界的每一个角落。」",
                "narrative_default": "亚历山大注视着你：「你的话很有意思。如果你能给我一个忠告，你会说什么？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "陛下应该注意身体健康，不要过度操劳。",
                        "consequence": "亚历山大若有所思",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "请为帝国培养合格的继承人。",
                        "consequence": "亚历山大叹了口气",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "征服之路自有天意，陛下顺其自然即可。",
                        "consequence": "亚历山大微微点头",
                        "timeline_change": False,
                        "next_round": 3,
                        "mood": "agree"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "亚历山大摸了摸额头：「身体……最近确实经常发烧。你说得对，我应该更注意。但东方还有太多土地等着我去征服。」\n\n时空开始扭曲，营帐的灯火渐渐模糊……",
                "narrative_disagree": "亚历山大望着远方：「继承人……我还没有子嗣。你说得对，我需要为帝国的未来做打算。」\n\n时空开始扭曲，战鼓声渐渐远去……",
                "narrative_default": "亚历山大最后说道：「无论命运如何，我亚历山大绝不会停下脚步。如果生命只有一次，那就让它燃烧到最亮！」\n\n你感到时空的洪流将你带回了未来……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】亚历山大在32岁时病逝于巴比伦，庞大的帝国随即分裂为三个继业者王国。但他的东征开启了希腊化时代，东西方文明在征服与被征服中实现了前所未有的融合。",
            "altered": "【平行时间线】亚历山大听取了你的忠告，注意身体健康并培养了继承人。他的帝国得以延续更久，希腊化时代的文明交融达到了前所未有的高度……"
        }
    },

    "industrial_revolution": {
        "npc_name": "詹姆斯·瓦特",
        "npc_role": "发明家",
        "npc_symbol": "⚙",
        "opening": "你好，陌生人！你来得正好——看看这台蒸汽机！我刚刚改进了它的冷凝器，效率提升了一倍！这将改变整个世界！",
        "context": "1769年，詹姆斯·瓦特改进了蒸汽机，这标志着工业革命的重要突破。机器开始取代人力，人类社会即将进入全新的时代。",
        "rounds": [
            {
                "round": 1,
                "narrative": "在一间烟雾弥漫的工坊里，瓦特正对着一台巨大的蒸汽机兴奋不已。铜制的管道在火光下闪闪发亮，蒸汽嘶嘶作响。\n\n「先生，你知道这意味着什么吗？一台蒸汽机可以顶替一百个工人的劳动！整个英国的工厂都会被革命！」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "这确实是伟大的发明，它将开启一个全新的时代！",
                        "consequence": "瓦特兴奋地拍着蒸汽机",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "agree"
                    },
                    {
                        "choice_id": "b",
                        "text": "但是，机器会取代工人的工作，他们会失业的……",
                        "consequence": "瓦特停下手中的工作",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "disagree"
                    },
                    {
                        "choice_id": "c",
                        "text": "蒸汽机燃烧煤炭，这会污染空气……未来的世界会为此付出代价。",
                        "consequence": "瓦特困惑地看着你",
                        "timeline_change": False,
                        "next_round": 2,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 2,
                "narrative_agree": "瓦特激动地挥舞着手臂：「没错！蒸汽机将不仅用于纺织厂，还可以驱动火车、轮船，甚至整个城市的运转！人类将征服距离和时间！」",
                "narrative_disagree": "瓦特皱起眉头：「失业？但效率提升意味着更多财富，更多工厂，最终会创造更多的工作。你说的'工人'……他们总可以学会操作机器。」",
                "narrative_thoughtful": "瓦特走出工坊，看着灰蒙蒙的天空：「污染？你说得对，煤炭的烟确实难闻。但与人力和畜力相比，蒸汽机是唯一的进步方向。难道你要我放弃？」",
                "narrative_default": "瓦特沉思片刻：「你的话让我思考。蒸汽机是不可阻挡的，但也许我们可以让它变得更好。你有什么建议？」",
                "choices": [
                    {
                        "choice_id": "a",
                        "text": "请考虑为工人设立保护法，不要让进步只属于少数人。",
                        "consequence": "瓦特认真地点了点头",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "b",
                        "text": "尝试寻找比煤炭更清洁的能源来驱动蒸汽机。",
                        "consequence": "瓦特露出惊讶的表情",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    },
                    {
                        "choice_id": "c",
                        "text": "让蒸汽机的发明保持开放，不要被垄断。",
                        "consequence": "瓦特似乎在认真考虑",
                        "timeline_change": True,
                        "next_round": 3,
                        "mood": "thoughtful"
                    }
                ]
            },
            {
                "round": 3,
                "narrative_agree": "瓦特微笑着说：「你说得对，进步应该属于所有人。我会把这个想法告诉博尔顿，我们可以在合同中加入让工人受益的条款。」\n\n工坊里的蒸汽渐渐模糊了你的视野，时空开始扭曲……",
                "narrative_disagree": "瓦特摇摇头：「清洁能源？目前还没有比煤炭更好的选择。但我记住了你的话，也许未来会有人找到答案。」\n\n蒸汽机的轰鸣声渐渐远去，你被卷入了时间的漩涡……",
                "narrative_default": "瓦特最后说道：「不管怎样，这台蒸汽机已经改变了历史。未来的事，就交给未来的人吧。」\n\n你感到一阵温暖的蒸汽包裹了你，然后一切归于寂静……",
                "choices": []
            }
        ],
        "endings": {
            "historical": "【历史定论】蒸汽机的发明开启了工业革命，英国成为'世界工厂'。但工业化也带来了严重的环境污染、童工问题和贫富分化，工人阶级的苦难持续了近百年才通过社会改革得到缓解。",
            "altered": "【平行时间线】瓦特受到了你的启发，在推广蒸汽机的同时推动了工人保护法规的制定。工业革命带来的进步惠及了更多人，环境问题也得到了更早的关注。这或许是另一个更好的世界……"
        }
    }
}


def get_script(event_id: str) -> Optional[dict]:
    return DIALOGUE_SCRIPTS.get(event_id)


def get_available_events() -> list:
    return [
        {"event_id": eid, "npc_name": s["npc_name"], "npc_role": s["npc_role"]}
        for eid, s in DIALOGUE_SCRIPTS.items()
    ]


def generate_opening(event_id: str) -> Optional[dict]:
    script = get_script(event_id)
    if not script:
        return None

    first_round = script["rounds"][0] if script["rounds"] else None
    if not first_round:
        return None

    return {
        "npc_name": script["npc_name"],
        "npc_role": script["npc_role"],
        "npc_symbol": script["npc_symbol"],
        "context": script["context"],
        "narrative": first_round["narrative"],
        "choices": first_round.get("choices", []),
        "round": 1
    }


def process_choice(
    event_id: str,
    choice_id: str,
    current_round: int,
    choices_made: list
) -> Optional[dict]:
    script = get_script(event_id)
    if not script:
        return None

    total_rounds = len(script["rounds"])

    if current_round >= total_rounds:
        return _build_ending(script, choices_made)

    current_round_data = script["rounds"][current_round - 1]

    selected_choice = None
    for c in current_round_data.get("choices", []):
        if c["choice_id"] == choice_id:
            selected_choice = c
            break

    if not selected_choice:
        return None

    new_mood = selected_choice.get("mood", "default")
    timeline_change = selected_choice.get("timeline_change", False)

    new_choices_made = choices_made + [{
        "round": current_round,
        "choice_id": choice_id,
        "choice_text": selected_choice["text"],
        "consequence": selected_choice["consequence"],
        "mood": new_mood
    }]

    next_round_num = current_round + 1

    if next_round_num > total_rounds:
        return _build_ending(script, new_choices_made)

    next_round_data = script["rounds"][next_round_num - 1]

    mood_key = f"narrative_{new_mood}"
    narrative = next_round_data.get(mood_key) or next_round_data.get("narrative_default", "")

    choices = next_round_data.get("choices", [])

    if not choices:
        ending = _build_ending(script, new_choices_made)
        full_narrative = f"*{selected_choice['consequence']}*\n\n{narrative}\n\n---\n\n{ending['narrative']}"
        return {
            "narrative": full_narrative,
            "choices": [],
            "round": next_round_num,
            "timeline_change": timeline_change,
            "mood": new_mood,
            "is_ending": True,
            "ending_type": ending.get("ending_type", "historical"),
            "choices_summary": ending.get("choices_summary", [])
        }

    return {
        "narrative": f"*{selected_choice['consequence']}*\n\n{narrative}",
        "choices": choices,
        "round": next_round_num,
        "timeline_change": timeline_change,
        "mood": new_mood,
        "is_ending": False
    }


def process_free_text(event_id: str, message: str, current_round: int, choices_made: list) -> dict:
    script = get_script(event_id)
    if not script:
        return {
            "narrative": "时空的干扰太大了，你的话无法传达给对方。",
            "choices": [],
            "round": current_round,
            "timeline_change": False,
            "is_ending": False
        }

    msg_lower = message.lower()

    keyword_responses = {
        "qin_unification": [
            (["统一", "六国", "征服"], "秦始皇点头道：「统一六国是朕毕生的夙愿。每一寸土地都是将士们用鲜血换来的。」"),
            (["长城", "匈奴"], "秦始皇指向北方：「匈奴是大秦的心腹之患。朕已经下令修筑长城，将他们挡在关外。」"),
            (["焚书", "坑儒", "文字"], "秦始皇面色一沉：「那些儒生以古非今，不焚书何以统一思想？统一文字更是千秋功业！」"),
            (["长生", "不死", "仙药"], "秦始皇叹息道：「徐福已经出海为朕寻找仙药了……你相信世间真有长生不老之术吗？」"),
            (["扶苏", "继承", "太子"], "秦始皇沉默良久：「扶苏……他太像那些儒生了。朕需要一个铁腕的继承者。」"),
        ],
        "shangyang_reform": [
            (["变法", "改革", "法律"], "商鞅点头道：「变法是秦国强大的唯一道路。旧制度束缚了生产力，必须打破！」"),
            (["严苛", "残酷", "苦"], "商鞅正色道：「乱世用重典！只有严法才能让百姓知道什么是该做的，什么是不该做的。」"),
            (["贵族", "旧势力", "反对"], "商鞅冷笑：「那些旧贵族不过是寄生虫。新法让他们失去了特权，他们当然恨我。」"),
            (["下场", "死", "命运"], "商鞅沉默片刻：「我知道……但我已经做好了为变法献身的准备。」"),
        ],
        "han_empire": [
            (["刘邦", "皇帝", "汉朝"], "刘邦自豪地说：「朕从一介布衣做到皇帝，这可是前无古人的事！」"),
            (["项羽", "楚汉", "战争"], "刘邦表情变得复杂：「项羽……他是个英雄，但不是个好帝王。输给朕不冤。」"),
            (["萧何", "张良", "韩信"], "刘邦笑道：「这三个人是朕最得力的助手。没有他们，朕打不下这江山。」"),
            (["休养", "百姓", "民生"], "刘邦认真地说：「百姓确实需要歇歇了。打来打去，受苦的都是老百姓。」"),
        ],
        "roman_empire": [
            (["共和", "元老院", "民主"], "奥古斯都摇头：「共和？元老院的腐败已经让罗马千疮百孔。帝制是唯一的出路。」"),
            (["凯撒", "刺杀", "布鲁图"], "奥古斯都眼神变得锐利：「布鲁图他们以为杀了凯撒就能拯救共和，结果只换来了更多的内战。」"),
            (["和平", "繁荣", "文化"], "奥古斯都骄傲地说：「罗马和平！这正是朕为之奋斗的目标。让罗马的子民不再流血。」"),
            (["继承", "继位", "继承人"], "奥古斯都叹了口气：「继承人……提比略不是最好的选择，但目前朕别无他法。」"),
        ],
        "alexander_east": [
            (["帝国", "征服", "东方"], "亚历山大兴奋地说：「东方！波斯、印度……我一定要打到世界的尽头！」"),
            (["希腊", "文明", "文化"], "亚历山大自豪地说：「希腊文明是世界上最伟大的文明！我要让它传遍全世界。」"),
            (["死亡", "命运", "寿命"], "亚历山大沉默了一瞬：「死亡……我不怕死，但我怕死前还有太多事没做完。」"),
            (["继承", "后继", "帝国分裂"], "亚历山大叹息：「我的将军们……他们各怀心思。如果我不在了，帝国恐怕会分裂。」"),
        ],
        "french_revolution": [
            (["自由", "平等", "博爱"], "市民高呼：「自由、平等、博爱！这就是我们为之战斗的口号！」"),
            (["国王", "路易", "贵族"], "市民愤怒地说：「路易十六和那些贵族骑在我们头上太久了！他们不配拥有权力！」"),
            (["断头台", "恐怖", "杀戮"], "市民的声音低了下来：「断头台……罗伯斯庇尔说它是'革命的工具'。但说实话，我有些害怕。」"),
            (["拿破仑", "将军", "军队"], "市民压低声音：「拿破仑？他确实是个天才将军。但有人说他的野心不止于此……」"),
        ],
        "industrial_revolution": [
            (["蒸汽", "机器", "工厂"], "瓦特兴奋地说：「蒸汽机！这就是未来！它将改变一切——工厂、交通、甚至整个社会的面貌！」"),
            (["煤炭", "污染", "环境"], "瓦特望向窗外灰蒙蒙的天空：「煤炭的烟确实不太好闻。但目前还没有更好的替代品。」"),
            (["工人", "劳动", "失业"], "瓦特陷入沉思：「工人们……他们总要适应新的时代。但你说得对，我们不能忽视他们。」"),
            (["火车", "铁路", "交通"], "瓦特眼中放光：「火车！是的，我已经在构想了——用蒸汽机驱动的列车，可以在铁轨上飞驰！」"),
        ]
    }

    responses = keyword_responses.get(event_id, [])

    for keywords, response in responses:
        for kw in keywords:
            if kw in msg_lower:
                return {
                    "narrative": response,
                    "choices": _get_current_round_choices(script, current_round),
                    "round": current_round,
                    "timeline_change": False,
                    "is_ending": False
                }

    default_responses = {
        "qin_unification": "秦始皇皱眉看着你：「你说的话朕不太明白。但你的存在本身就是个奇迹——也许天意让你来此，必有深意。」",
        "shangyang_reform": "商鞅看着你：「你的话我听不太懂。但既然你能从未来而来，一定有你的道理。继续说吧。」",
        "han_empire": "刘邦好奇地看着你：「你说的啥？算了，反正你是从未来来的，说什么朕都不奇怪。」",
        "roman_empire": "奥古斯都审视着你：「有趣……你的话在朕的时代没有对应的概念。但朕愿意倾听——毕竟你能从未来而来，一定不简单。」",
        "alexander_east": "亚历山大好奇地看着你：「你的话有些我听不懂。但没关系——我亚历山大对一切未知的事物都充满好奇！」",
        "french_revolution": "市民困惑地看着你：「你说的我听不太懂。但没关系——革命需要每一个人的声音！继续说吧，公民！」",
        "industrial_revolution": "瓦特挠了挠头：「你说的这个词我没听过。不过你要是对蒸汽机感兴趣，我很乐意给你演示！」",
    }

    return {
        "narrative": default_responses.get(event_id, "对方似乎没有完全理解你的话，但仍在认真倾听。"),
        "choices": _get_current_round_choices(script, current_round),
        "round": current_round,
        "timeline_change": False,
        "is_ending": False
    }


def _get_current_round_choices(script: dict, current_round: int) -> list:
    if current_round <= len(script["rounds"]):
        return script["rounds"][current_round - 1].get("choices", [])
    return []


def process_post_ending(event_id: str, message: str) -> dict:
    script = get_script(event_id)
    if not script:
        return {
            "narrative": "时空的裂缝已经闭合，你无法再与过去对话。",
            "choices": [],
            "round": 0,
            "is_ending": True,
        }

    post_responses = {
        "qin_unification": [
            (["你好", "在吗", "还在"], "时空的回响中，隐约传来秦始皇的声音：「时空已闭，寡人与你的对话已成定数。但你的每一句话，都在历史的长河中留下了涟漪。」"),
            (["谢谢", "感谢", "再见"], "一道金色的光芒闪过，仿佛是始皇帝最后的注视：「后会有期，时空旅人。愿你记住这段经历。」"),
            (["改写", "改变", "历史"], "时空的回音微微震动：「你的选择已经在另一个时间线生效了。但在这个宇宙中，历史的车轮仍在前行……」"),
        ],
        "roman_empire": [
            (["你好", "在吗", "还在"], "大理石宫殿的回声渐渐传来：「对话已经结束了，旅人。但罗马的荣光将永远照耀。」"),
            (["谢谢", "感谢", "再见"], "一道光芒闪过：「愿诸神与你同在，时空旅人。罗马不会忘记你的来访。」"),
            (["改变", "历史", "帝国"], "时空的裂隙中回荡着奥古斯都的声音：「你的话语已在时间的织锦上留下了新的纹路。未来已经不同了。」"),
        ],
        "french_revolution": [
            (["你好", "在吗", "还在"], "巴黎街头的回声隐约可闻：「革命还在继续，公民！但我们的对话已经成为历史的一部分。」"),
            (["谢谢", "感谢", "再见"], "三色旗的光芒在时空中闪烁：「自由之路永不止息。感谢你的参与，公民！」"),
            (["改变", "革命", "未来"], "时空的回音微微震荡：「你的话已经在另一个时间线上激起了不同的浪潮。命运的齿轮在转动……」"),
        ],
        "shangyang_reform": [
            (["你好", "在吗", "还在"], "竹简的沙沙声在时空中回响：「变法已成定局，旅人。但你的建议让这个结局有了新的色彩。」"),
            (["谢谢", "感谢", "再见"], "烛火在时空中闪烁：「法之精神不灭。后会有期，远方的旅人。」"),
            (["改变", "变法", "秦国"], "时空的裂隙中传来商鞅的声音：「你的话语已经改变了另一条时间线上的秦国。变法的种子在那里开出了不同的花。」"),
        ],
        "han_empire": [
            (["你好", "在吗", "还在"], "宫殿的回声在时空中荡漾：「大汉还在，旅人！我们的对话已成佳话。」"),
            (["谢谢", "感谢", "再见"], "龙椅上的光影微微闪烁：「从布衣到帝王，朕这辈子值了。后会有期！」"),
            (["改变", "历史", "汉朝"], "时空的回音中带着刘邦的笑声：「你的话在另一条时间线上改变了大汉的命运。有意思！」"),
        ],
        "alexander_east": [
            (["你好", "在吗", "还在"], "营帐的灯火在时空的尽头闪烁：「征服虽然结束了，但我亚历山大的传说永远不会停息。」"),
            (["谢谢", "感谢", "再见"], "战鼓声在远方回荡：「愿阿喀琉斯的荣光与你同在，时空旅人。」"),
            (["改变", "帝国", "命运"], "时空的裂隙中传来亚历山大的声音：「你的话语在我的帝国中激起了不同的回响。也许在另一条时间线上，我活过了32岁。」"),
        ],
        "industrial_revolution": [
            (["你好", "在吗", "还在"], "蒸汽机的轰鸣在时空中隐约回响：「虽然对话结束了，但进步的齿轮永远在转动。」"),
            (["谢谢", "感谢", "再见"], "温暖的蒸汽拂过你的脸庞：「感谢你的建议，旅人。也许未来真的会因为今天的对话而不同。」"),
            (["改变", "工业", "未来"], "时空的回音中混着机械声：「你的想法已经改变了另一条时间线上工业革命的走向。蒸汽的力量将带来不同的未来……」"),
        ],
    }

    msg_lower = message.lower()
    responses = post_responses.get(event_id, [])

    for keywords, response in responses:
        for kw in keywords:
            if kw in msg_lower:
                return {
                    "narrative": response,
                    "choices": [],
                    "round": 0,
                    "is_ending": True,
                }

    post_defaults = {
        "qin_unification": "时空的回响中传来秦始皇最后的话语：「寡人的帝国会延续下去，而你，将带着这段记忆回到未来。好好珍惜吧。」",
        "roman_empire": "奥古斯都的声音在时空中渐渐远去：「愿罗马的荣光永远照耀你的道路。再会了，旅人。」",
        "french_revolution": "巴黎的钟声在时空的尽头回荡：「自由、平等、博爱——这不仅仅是口号，更是我们为之奋斗的理想。带着它回到你的时代吧。」",
        "shangyang_reform": "烛火在时空中渐渐熄灭：「变法之道，在于知行合一。你的建议我已经记下了。后会有期。」",
        "han_empire": "刘邦的声音从远处传来：「哈哈，你这个从未来来的人还挺有意思的！朕记住你了。回去吧！」",
        "alexander_east": "亚历山大的声音从远方传来：「命运不可改变，但你的勇气令人敬佩。也许在另一个宇宙中，我们会再次相遇。」",
        "industrial_revolution": "瓦特的声音在蒸汽中回荡：「进步永不停息！把你的想法带到未来去实现吧，旅人。」",
    }

    return {
        "narrative": post_defaults.get(event_id, "时空的裂缝正在愈合。这段对话已经成为了历史的一部分，而你，即将回到属于自己的时代。"),
        "choices": [],
        "round": 0,
        "is_ending": True,
    }


def _build_ending(script: dict, choices_made: list) -> dict:
    has_timeline_change = any(c.get("timeline_change") or c.get("mood") == "thoughtful" for c in choices_made)

    if has_timeline_change:
        ending_type = "altered"
    else:
        ending_type = "historical"

    ending_text = script["endings"].get(ending_type, script["endings"]["historical"])

    choices_summary = []
    for c in choices_made:
        choices_summary.append({
            "round": c["round"],
            "text": c.get("choice_text", ""),
            "consequence": c.get("consequence", "")
        })

    return {
        "narrative": ending_text,
        "choices": [],
        "round": 0,
        "timeline_change": has_timeline_change,
        "mood": "ending",
        "is_ending": True,
        "ending_type": ending_type,
        "choices_summary": choices_summary
    }


def has_timeline_change(mood: str, timeline_change: bool) -> bool:
    return timeline_change or mood == "thoughtful"


def calculate_timeline_branches(choices_made: list) -> list:
    branches = []
    for c in choices_made:
        if c.get("mood") == "thoughtful" or c.get("timeline_change"):
            branches.append({
                "branch_point": f"Round {c['round']}",
                "original": "Following the historical path",
                "altered": c.get("consequence", "A different choice was made"),
                "choice_text": c.get("choice_text", "")
            })
    return branches
