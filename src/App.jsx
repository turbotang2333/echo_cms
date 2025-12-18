import React, { useState, useEffect } from 'react';
import { 
  Users, 
  Star, 
  Import, 
  MessageSquare, 
  ThumbsUp, 
  Megaphone, 
  Clock, 
  MessageCircle,
  TrendingUp,
  Gamepad2,
  MoreHorizontal,
  ArrowUpRight,
  ArrowDownRight,
  MonitorPlay,
  Hash,       
  Heart,       
  LayoutList,
  Activity,
  AlertCircle,
  Settings
} from 'lucide-react';
import ConfigModal from './components/ConfigModal';

// ==========================================
// 1. 配置与常量 (Configuration)
// ==========================================

// 平台元数据配置
const PLATFORM_CONFIG = [
  { id: 'taptap', label: 'Tap', icon: LayoutList, color: 'text-emerald-500' },
  { id: 'bilibili', label: 'B站', icon: MonitorPlay, color: 'text-pink-400' },
  { id: 'weibo', label: '微博', icon: Hash, color: 'text-red-500' },
  { id: 'xiaohongshu', label: '红书', icon: Heart, color: 'text-rose-500' },
];

// 周期配置
const PERIOD_OPTIONS = [
  { id: 'day', label: '日' },
  { id: 'week', label: '周' },
  { id: 'month', label: '月' },
];

// ==========================================
// 2. 默认/Fallback 数据
// ==========================================
// 用于在 data.json 加载失败或本地开发时的兜底展示
const FALLBACK_DATA = [
  {
    "id": "demo",
    "name": "示例游戏 (数据加载中)",
    "icon_char": "示",
    "fetch_status": {
      "taptap": "not_configured",
      "bilibili": "not_configured",
      "weibo": "not_configured",
      "xiaohongshu": "not_configured"
    },
    "basic_info": {
      "rating": "0.0",
      "tags": ["加载中"],
      "reservations": "-",
      "followers": "-",
      "review_count": "-",
      "status": "连接中",
      "diffs": {}
    },
    "official_posts": {},
    "hot_reviews": [],
    "last_updated": "-"
  }
];

// ==========================================
// 3. 通用 UI 组件 (UI Components)
// ==========================================

const SectionCard = ({ children, className = "" }) => (
  <div className={`bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden flex flex-col ${className}`}>
    {children}
  </div>
);

const SectionHeader = ({ icon: Icon, title, rightElement, iconColor = "text-slate-500", iconBg = "bg-slate-100" }) => (
  <div className="flex-none flex items-center justify-between p-4 pb-3 border-b border-slate-50 bg-white">
    <div className="flex items-center gap-2">
      <div className={`p-1.5 rounded-md ${iconBg}`}>
        <Icon className={`w-4 h-4 ${iconColor}`} />
      </div>
      <h4 className="font-bold text-sm text-slate-800">{title}</h4>
    </div>
    {rightElement}
  </div>
);

// 指标卡片：包含数值和涨跌幅逻辑
const MiniStat = ({ label, value, diff, icon: Icon, colorClass }) => {
  const isPositive = diff?.includes('+');
  const isNegative = diff?.includes('-');
  const isZero = !isPositive && !isNegative;
  
  let diffStyles = "text-slate-400";
  let DiffIcon = null;
  
  if (isPositive) { 
    diffStyles = "text-emerald-600 bg-emerald-50"; 
    DiffIcon = ArrowUpRight; 
  } else if (isNegative) { 
    diffStyles = "text-rose-600 bg-rose-50"; 
    DiffIcon = ArrowDownRight; 
  }

  return (
    <div className="bg-slate-50 p-3 rounded-lg border border-slate-100 flex items-center justify-between group hover:border-slate-200 transition-colors">
      <div>
        <p className="text-[10px] text-slate-400 uppercase tracking-wider font-bold mb-0.5">{label}</p>
        <div className="flex items-baseline gap-2">
          <p className="text-sm font-bold text-slate-700">{value || '-'}</p>
          {diff && !isZero && (
            <div className={`flex items-center text-[10px] font-bold px-1 rounded ${diffStyles}`}>
              {DiffIcon && <DiffIcon className="w-2.5 h-2.5 mr-0.5" />}
              {diff}
            </div>
          )}
        </div>
      </div>
      <Icon className={`w-4 h-4 opacity-50 group-hover:opacity-100 transition-opacity ${colorClass}`} />
    </div>
  );
};

// 官方动态 Item
const CompactTimelineItem = ({ post }) => (
  <div className={`relative pl-4 border-l-2 pb-4 last:pb-0 last:border-l-0 transition-all ${
    post.is_new ? 'border-indigo-200' : 'border-slate-100'
  }`}>
    <div className={`absolute -left-[5px] top-1.5 w-2 h-2 rounded-full ring-2 ring-white ${
      post.is_new ? 'bg-indigo-500 animate-pulse' : 'bg-slate-300'
    }`}></div>
    
    <div className="flex items-center gap-2 mb-1">
      <p className="text-xs text-slate-400 font-mono">{post.date}</p>
      {post.is_new && (
        <span className="text-[9px] font-bold bg-indigo-100 text-indigo-600 px-1.5 rounded-sm border border-indigo-200">
          NEW
        </span>
      )}
    </div>
    
    <h4 className={`text-sm font-medium leading-snug hover:text-indigo-600 cursor-pointer mb-2 ${
      post.is_new ? 'text-slate-800' : 'text-slate-500'
    }`}>
      {post.title}
    </h4>
    
    <div className="flex items-center gap-3 text-xs text-slate-400">
      <span className="flex items-center gap-1 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-100"><MessageSquare className="w-3 h-3" /> {post.comments}</span>
      <span className="flex items-center gap-1 bg-slate-50 px-1.5 py-0.5 rounded border border-slate-100"><ThumbsUp className="w-3 h-3" /> {post.likes}</span>
    </div>
  </div>
);

// 评论 Item
const CompactReviewItem = ({ review }) => (
  <div className={`p-3 rounded-lg border mb-2 last:mb-0 transition-all ${
    review.is_new 
      ? 'bg-amber-50 border-amber-200' 
      : 'bg-slate-50 border-slate-100 hover:border-slate-200'
  }`}>
    <div className="flex justify-between items-center mb-1.5">
      <div className="flex items-center gap-2">
        <span className={`text-xs font-bold truncate max-w-[100px] ${review.is_new ? 'text-amber-900' : 'text-slate-600'}`}>
          {review.user}
        </span>
        {review.is_new && (
          <span className="text-[9px] bg-amber-100 text-amber-700 px-1 rounded border border-amber-200">
            新热评
          </span>
        )}
      </div>
      <div className="flex text-yellow-400 scale-75 origin-right">
        {[...Array(5)].map((_, i) => (
          <Star key={i} className={`w-3 h-3 ${i < review.score ? 'fill-current' : 'text-slate-200'}`} />
        ))}
      </div>
    </div>
    <p className={`text-xs leading-relaxed mb-2 line-clamp-3 ${review.is_new ? 'text-slate-800 font-medium' : 'text-slate-600'}`}>
      {review.content}
    </p>
    <div className="flex items-center gap-3 text-[10px] text-slate-400">
      <span className={review.is_new ? 'text-amber-700/60' : ''}>{review.replies} 回复</span>
      <span className={review.is_new ? 'text-amber-700/60' : ''}>{review.likes} 点赞</span>
    </div>
  </div>
);

// 平台状态内容组件
const PlatformContent = ({ game, activePlatform }) => {
  const fetchStatus = game.fetch_status?.[activePlatform];
  const currentPosts = game.official_posts?.[activePlatform] || [];
  const platformLabel = PLATFORM_CONFIG.find(p => p.id === activePlatform)?.label;

  // 状态：未配置
  if (fetchStatus === 'not_configured') {
    return (
      <div className="h-full flex flex-col items-center justify-center text-slate-400 py-6">
        <Settings className="w-8 h-8 mb-2 opacity-20" />
        <p className="text-xs font-medium text-slate-500">暂未配置此平台</p>
        <p className="text-[10px] text-slate-400 mt-1">请在配置管理中添加链接</p>
      </div>
    );
  }

  // 状态：抓取失败
  if (fetchStatus === 'failed') {
    return (
      <div className="h-full flex flex-col items-center justify-center py-6">
        <AlertCircle className="w-8 h-8 mb-2 text-red-300" />
        <p className="text-xs font-medium text-red-600">抓取失败</p>
        <p className="text-[10px] text-red-400 mt-1">请检查链接配置是否正确</p>
      </div>
    );
  }

  // 状态：数据过期 (stale) - 显示警告条 + 数据
  if (fetchStatus === 'stale') {
    return (
      <div className="flex-1 flex flex-col">
        <div className="bg-amber-50 border-b border-amber-100 px-3 py-1.5 flex items-center gap-2">
          <AlertCircle className="w-3 h-3 text-amber-500" />
          <span className="text-[10px] text-amber-700 font-medium">数据可能已过期</span>
        </div>
        <div className="p-4 flex-1">
          {currentPosts.length > 0 ? (
            <div className="space-y-1">
              {currentPosts.map((post, idx) => (
                <CompactTimelineItem key={idx} post={post} />
              ))}
            </div>
          ) : (
            <div className="h-full flex flex-col items-center justify-center text-slate-400 py-4">
              <Megaphone className="w-8 h-8 mb-2 opacity-10" />
              <p className="text-[10px]">暂无 {platformLabel} 动态</p>
            </div>
          )}
        </div>
      </div>
    );
  }

  // 状态：成功 (success) 或默认
  return (
    <div className="p-4 flex-1">
      {currentPosts.length > 0 ? (
        <div className="space-y-1">
          {currentPosts.map((post, idx) => (
            <CompactTimelineItem key={idx} post={post} />
          ))}
        </div>
      ) : (
        <div className="h-full flex flex-col items-center justify-center text-slate-400 py-4">
          <Megaphone className="w-8 h-8 mb-2 opacity-10" />
          <p className="text-[10px]">暂无 {platformLabel} 动态</p>
        </div>
      )}
    </div>
  );
};

// ==========================================
// 4. 核心业务组件: GameColumn
// ==========================================

const GameColumn = ({ game, comparisonPeriod, setComparisonPeriod, activePlatform, setActivePlatform }) => {
  return (
    <div className="flex-none w-[380px] flex flex-col bg-slate-50/50 rounded-xl shadow-md border border-slate-200 overflow-hidden h-full">
      {/* 4.1 产品信息头部 */}
      <div className="flex-none p-4 border-b border-slate-100 bg-white z-10">
        <div className="flex justify-between items-start mb-3">
          <div className="flex gap-3">
            <div className="w-12 h-12 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-xl font-bold text-slate-600 shadow-inner">
              {game.icon_char || game.name[0]}
            </div>
            <div>
              <h3 className="font-bold text-lg text-slate-900 leading-tight">{game.name}</h3>
              <div className="flex items-center gap-2 mt-1">
                <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded border ${
                  game.basic_info.status === '预约中' 
                    ? 'bg-emerald-50 text-emerald-600 border-emerald-100' 
                    : 'bg-indigo-50 text-indigo-600 border-indigo-100'
                }`}>
                  {game.basic_info.status}
                </span>
                <div className="flex items-center text-yellow-500 gap-0.5">
                    <Star className="w-3 h-3 fill-current" />
                    <span className="text-xs font-bold">{game.basic_info.rating}</span>
                </div>
              </div>
            </div>
          </div>
          <button className="text-slate-300 hover:text-slate-500">
            <MoreHorizontal className="w-5 h-5" />
          </button>
        </div>
        
        <div className="flex flex-wrap gap-1.5 mb-1">
          {game.basic_info.tags?.slice(0, 3).map(tag => (
            <span key={tag} className="text-[10px] px-1.5 py-0.5 bg-slate-50 text-slate-500 rounded border border-slate-100">
              {tag}
            </span>
          ))}
        </div>
      </div>

      {/* 4.2 滚动内容区域 */}
      <div className="flex-1 overflow-y-auto custom-scrollbar p-4 space-y-4">
        
        {/* 板块 A: 基础数据监控 */}
        <SectionCard>
          <SectionHeader 
            icon={Activity} 
            title="基础数据" 
            iconColor="text-blue-600"
            iconBg="bg-blue-50"
            rightElement={
              <div className="flex bg-slate-100 p-0.5 rounded-lg border border-slate-200 scale-90 origin-right">
                {PERIOD_OPTIONS.map(p => (
                  <button
                    key={p.id}
                    onClick={() => setComparisonPeriod(p.id)}
                    className={`px-2 py-0.5 text-[10px] font-medium rounded-md transition-all ${
                      comparisonPeriod === p.id 
                        ? 'bg-white text-indigo-600 shadow-sm ring-1 ring-black/5' 
                        : 'text-slate-400 hover:text-slate-600'
                    }`}
                  >
                    {p.label}
                  </button>
                ))}
              </div>
            }
          />
          <div className="p-3 grid grid-cols-2 gap-2">
            <MiniStat 
              label="预约总数" 
              value={game.basic_info.reservations} 
              diff={game.basic_info.diffs?.reservations?.[comparisonPeriod]}
              icon={TrendingUp} 
              colorClass="text-emerald-500" 
            />
            <MiniStat 
              label="关注人数" 
              value={game.basic_info.followers} 
              diff={game.basic_info.diffs?.followers?.[comparisonPeriod]}
              icon={Users} 
              colorClass="text-blue-500" 
            />
            <MiniStat 
              label="累计评价" 
              value={game.basic_info.review_count} 
              diff={game.basic_info.diffs?.review_count?.[comparisonPeriod]}
              icon={MessageSquare} 
              colorClass="text-purple-500" 
            />
            <MiniStat 
              label="评分趋势" 
              value={game.basic_info.rating} 
              diff={game.basic_info.diffs?.rating?.[comparisonPeriod]}
              icon={Star} 
              colorClass="text-yellow-500" 
            />
          </div>
        </SectionCard>

        {/* 板块 B: 官方运营动态 */}
        <SectionCard className="min-h-[220px]">
          <SectionHeader 
            icon={Megaphone} 
            title="官方动态" 
            iconColor="text-indigo-600"
            iconBg="bg-indigo-50"
          />
          
          {/* 平台 Tab 栏 */}
          <div className="flex border-b border-slate-50 bg-slate-50/30">
            {PLATFORM_CONFIG.map(p => {
              const Icon = p.icon;
              const isActive = activePlatform === p.id;
              const status = game.fetch_status?.[p.id];
              
              return (
                <button
                  key={p.id}
                  onClick={() => setActivePlatform(p.id)}
                  className={`flex-1 py-2 flex items-center justify-center gap-1.5 text-[10px] font-bold transition-all relative ${
                    isActive ? 'text-slate-800 bg-white shadow-sm' : 'text-slate-400 hover:text-slate-600 hover:bg-slate-50'
                  }`}
                >
                  <Icon className={`w-3 h-3 ${isActive ? p.color : 'text-slate-400'}`} />
                  {p.label}
                  {/* 状态指示点 */}
                  {status === 'failed' && (
                    <span className="absolute top-1 right-2 w-1.5 h-1.5 bg-red-500 rounded-full"></span>
                  )}
                  {status === 'stale' && (
                    <span className="absolute top-1 right-2 w-1.5 h-1.5 bg-amber-500 rounded-full"></span>
                  )}
                  {isActive && <div className="absolute top-0 left-0 right-0 h-0.5 bg-indigo-500"></div>}
                </button>
              )
            })}
          </div>

          <PlatformContent game={game} activePlatform={activePlatform} />
        </SectionCard>

        {/* 板块 C: 热门舆情 */}
        <SectionCard className="min-h-[200px]">
          <SectionHeader 
             icon={MessageCircle} 
             title="热门舆情" 
             iconColor="text-rose-600"
             iconBg="bg-rose-50"
             rightElement={
                <span className="text-[10px] font-bold text-amber-600 bg-amber-50 px-2 py-0.5 rounded-full border border-amber-100">
                 Tap本周热评
               </span>
             }
          />
          <div className="p-3">
            {game.hot_reviews?.length > 0 ? (
              <div>
                {game.hot_reviews.map((review, idx) => (
                  <CompactReviewItem key={idx} review={review} />
                ))}
              </div>
            ) : (
              <div className="py-8 text-center text-slate-400 text-[10px] border border-dashed border-slate-100 rounded-lg bg-slate-50">
                暂无评论采集
              </div>
            )}
          </div>
        </SectionCard>

      </div>
    </div>
  );
};

// ==========================================
// 5. 主应用入口 (Main App)
// ==========================================

export default function App() {
  const [games, setGames] = useState(FALLBACK_DATA); // 默认显示 Fallback
  const [loading, setLoading] = useState(true);
  const [lastUpdated, setLastUpdated] = useState('-');

  // 模态框逻辑
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  
  // 配置管理模态框
  const [isConfigModalOpen, setIsConfigModalOpen] = useState(false);
  const [gamesConfig, setGamesConfig] = useState([]);
  
  // 全局状态
  const [comparisonPeriod, setComparisonPeriod] = useState('day');
  const [globalPlatform, setGlobalPlatform] = useState('taptap'); 

  // 数据获取：GitHub Pages 模式
  useEffect(() => {
    fetch('./data.json')
      .then(res => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(data => {
        setGames(data);
        if(data[0]?.last_updated) setLastUpdated(data[0].last_updated);
        setLoading(false);
      })
      .catch(err => {
        console.log("本地开发或未找到 data.json，使用默认数据:", err);
        setLoading(false);
      });
  }, []);

  // 加载游戏配置
  useEffect(() => {
    fetch('./games_config.json')
      .then(res => {
        if (!res.ok) throw new Error('Not found');
        return res.json();
      })
      .then(data => {
        setGamesConfig(data);
      })
      .catch(err => {
        console.log("未找到 games_config.json，使用空配置:", err);
      });
  }, []);

  // 手动导入逻辑
  const handleImport = () => {
    try {
      const data = JSON.parse(jsonInput);
      if (Array.isArray(data)) {
        setGames(data);
        if(data[0]?.last_updated) setLastUpdated(data[0].last_updated);
        setIsModalOpen(false);
        setJsonInput('');
      } else {
        alert('格式错误: 需要 JSON 数组');
      }
    } catch (e) {
      alert('解析错误: JSON 格式无效');
    }
  };

  return (
    <div className="flex flex-col h-screen bg-slate-100 font-sans text-slate-800">
      
      {/* 顶部栏 */}
      <header className="flex-none bg-white border-b border-slate-200 px-6 py-3 flex justify-between items-center shadow-sm z-20">
        <div className="flex items-center gap-4">
          <div className="flex items-center gap-2">
            <div className="p-2 bg-indigo-50 rounded-lg">
              <Gamepad2 className="w-5 h-5 text-indigo-600" />
            </div>
            <h1 className="font-bold text-lg text-slate-800 tracking-tight">TapMonitor 竞品看板</h1>
          </div>
        </div>
        
        <div className="flex items-center gap-4">
          <span className="text-xs text-slate-400 hidden sm:inline-flex items-center gap-1">
            <Clock className="w-3 h-3" /> 数据更新: {lastUpdated}
          </span>
          <button 
            onClick={() => setIsConfigModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 border border-slate-300 hover:bg-slate-50 text-slate-700 rounded-md text-sm font-medium transition-colors"
          >
            <Settings className="w-4 h-4" /> 配置管理
          </button>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-sm font-medium transition-colors shadow-sm"
          >
            <Import className="w-4 h-4" /> 导入/调试
          </button>
        </div>
      </header>

      {/* 主内容区 */}
      <main className="flex-1 overflow-x-auto overflow-y-hidden">
        <div className="h-full flex p-6 gap-6 w-max">
          {games.map((game) => (
            <GameColumn 
              key={game.id} 
              game={game} 
              comparisonPeriod={comparisonPeriod} 
              setComparisonPeriod={setComparisonPeriod}
              activePlatform={globalPlatform} 
              setActivePlatform={setGlobalPlatform}
            />
          ))}

          {/* 占位按钮列 */}
          <div className="flex-none w-[100px] flex items-center justify-center">
             <button className="w-12 h-12 rounded-full bg-slate-200 hover:bg-slate-300 text-slate-500 flex items-center justify-center transition-colors">
               <span className="text-2xl font-light pb-1">+</span>
             </button>
          </div>
        </div>
      </main>

      {/* 导入模态框 */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-xl w-full max-w-lg p-6 shadow-2xl animate-in zoom-in-95 duration-200">
            <div className="flex justify-between items-center mb-4">
               <h3 className="font-bold text-lg">调试：导入 JSON 数据</h3>
               <button onClick={() => setIsModalOpen(false)} className="text-slate-400 hover:text-slate-600">✕</button>
            </div>
            <p className="text-xs text-slate-500 mb-2">手动粘贴爬虫生成的 JSON 数组以测试 UI：</p>
            <textarea
              className="w-full h-48 p-3 border border-slate-300 rounded-lg font-mono text-xs focus:ring-2 focus:ring-indigo-500 outline-none resize-none bg-slate-50"
              placeholder='[{"id": "...", "name": "...", "basic_info": { "diffs": {...} }, ...}]'
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
            ></textarea>
            <div className="flex justify-end gap-3 mt-4">
              <button onClick={() => setIsModalOpen(false)} className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium">取消</button>
              <button onClick={handleImport} className="px-4 py-2 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 shadow-md">确认更新看板</button>
            </div>
          </div>
        </div>
      )}

      {/* 配置管理模态框 */}
      <ConfigModal
        isOpen={isConfigModalOpen}
        onClose={(updatedConfig) => {
          setGamesConfig(updatedConfig);
          setIsConfigModalOpen(false);
        }}
        initialConfig={gamesConfig}
      />
    </div>
  );
}
