import React, { useState, useRef, useEffect } from 'react';
import { 
  X, 
  Plus, 
  Download, 
  Upload, 
  Save, 
  Trash2,
  Settings,
  AlertCircle,
  CheckCircle,
  Gamepad2
} from 'lucide-react';

/**
 * 配置管理弹窗组件
 * 功能：游戏配置的增删改查、导入导出
 */
export default function ConfigModal({ isOpen, onClose, initialConfig = [] }) {
  // 配置列表状态
  const [games, setGames] = useState(initialConfig);
  
  // 监听 initialConfig 变化，同步更新内部状态
  useEffect(() => {
    if (isOpen && initialConfig.length > 0) {
      setGames(initialConfig);
    }
  }, [isOpen, initialConfig]);
  
  // 当前选中的游戏索引
  const [selectedIndex, setSelectedIndex] = useState(null);
  
  // 编辑模式：'new' | 'edit' | null
  const [editMode, setEditMode] = useState(null);
  
  // 拖拽相关状态
  const [draggedIndex, setDraggedIndex] = useState(null);
  const [dragOverIndex, setDragOverIndex] = useState(null);
  
  // 表单数据
  const [formData, setFormData] = useState(getEmptyForm());
  
  // 表单验证错误
  const [errors, setErrors] = useState({});
  
  // 导入文件 input ref
  const fileInputRef = useRef(null);
  
  // 提示消息
  const [toast, setToast] = useState(null);

  // 生成空表单
  function getEmptyForm() {
    return {
      id: '',
      name: '',
      icon_url: '',
      enabled: true,
      platforms: {
        taptap: { url: '' },
        bilibili: { url: '' },
        weibo: { url: '' },
        xiaohongshu: { url: '' }
      },
      created_at: new Date().toISOString().split('T')[0]
    };
  }

  // 显示提示消息
  function showToast(message, type = 'success') {
    setToast({ message, type });
    setTimeout(() => setToast(null), 3000);
  }

  // 新增游戏
  function handleNew() {
    setEditMode('new');
    setSelectedIndex(null);
    setFormData(getEmptyForm());
    setErrors({});
  }

  // 选中游戏编辑
  function handleEdit(index) {
    setEditMode('edit');
    setSelectedIndex(index);
    setFormData(JSON.parse(JSON.stringify(games[index]))); // 深拷贝
    setErrors({});
  }

  // 表单字段变更
  function handleFieldChange(field, value) {
    setFormData(prev => ({ ...prev, [field]: value }));
    // 清除该字段的错误
    if (errors[field]) {
      setErrors(prev => ({ ...prev, [field]: null }));
    }
  }

  // 平台链接变更
  function handlePlatformChange(platform, value) {
    setFormData(prev => ({
      ...prev,
      platforms: {
        ...prev.platforms,
        [platform]: { url: value }
      }
    }));
  }

  // 表单验证
  function validateForm() {
    const newErrors = {};
    
    // 游戏名必填
    if (!formData.name.trim()) {
      newErrors.name = '游戏名称不能为空';
    }
    
    // ID 必填且唯一
    if (!formData.id.trim()) {
      newErrors.id = '游戏 ID 不能为空';
    } else {
      // 检查 ID 重复（编辑模式下排除自己）
      const isDuplicate = games.some((game, idx) => 
        game.id === formData.id && idx !== selectedIndex
      );
      if (isDuplicate) {
        newErrors.id = '游戏 ID 已存在';
      }
    }
    
    // URL 格式验证（简单检查）
    const urlFields = ['taptap', 'bilibili', 'weibo', 'xiaohongshu'];
    urlFields.forEach(platform => {
      const url = formData.platforms[platform].url;
      if (url && !url.startsWith('http')) {
        newErrors[platform] = '请输入完整的 URL（以 http:// 或 https:// 开头）';
      }
    });
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  }

  // 保存游戏
  function handleSave() {
    if (!validateForm()) {
      showToast('请修正表单错误', 'error');
      return;
    }
    
    if (editMode === 'new') {
      setGames([...games, formData]);
      showToast('游戏添加成功', 'success');
    } else {
      const updated = [...games];
      updated[selectedIndex] = formData;
      setGames(updated);
      showToast('游戏更新成功', 'success');
    }
    
    // 重置状态
    setEditMode(null);
    setSelectedIndex(null);
    setFormData(getEmptyForm());
  }

  // 删除游戏
  function handleDelete() {
    if (!window.confirm(`确定删除游戏"${formData.name}"吗？`)) {
      return;
    }
    
    const updated = games.filter((_, idx) => idx !== selectedIndex);
    setGames(updated);
    showToast('游戏删除成功', 'success');
    
    // 重置状态
    setEditMode(null);
    setSelectedIndex(null);
    setFormData(getEmptyForm());
  }

  // 取消编辑
  function handleCancel() {
    setEditMode(null);
    setSelectedIndex(null);
    setFormData(getEmptyForm());
    setErrors({});
  }

  // 导出配置
  function handleExport() {
    try {
      const json = JSON.stringify(games, null, 2);
      const blob = new Blob([json], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'games_config.json';
      a.click();
      URL.revokeObjectURL(url);
      showToast('配置导出成功', 'success');
    } catch (err) {
      showToast('导出失败: ' + err.message, 'error');
    }
  }

  // 导入配置
  function handleImport() {
    fileInputRef.current?.click();
  }

  // 处理文件上传
  function handleFileChange(e) {
    const file = e.target.files[0];
    if (!file) return;
    
    const reader = new FileReader();
    reader.onload = (event) => {
      try {
        const data = JSON.parse(event.target.result);
        if (!Array.isArray(data)) {
          throw new Error('配置文件格式错误：需要 JSON 数组');
        }
        setGames(data);
        showToast(`成功导入 ${data.length} 个游戏配置`, 'success');
        
        // 重置状态
        setEditMode(null);
        setSelectedIndex(null);
        setFormData(getEmptyForm());
      } catch (err) {
        showToast('导入失败: ' + err.message, 'error');
      }
    };
    reader.readAsText(file);
    
    // 重置 input 以便同一文件可以重复上传
    e.target.value = '';
  }

  // 确认并关闭
  function handleConfirm() {
    onClose(games); // 将配置传递回父组件
  }

  // 拖拽开始
  function handleDragStart(index) {
    setDraggedIndex(index);
  }

  // 拖拽经过
  function handleDragOver(e, index) {
    e.preventDefault(); // 必须阻止默认行为才能允许 drop
    if (draggedIndex === null || draggedIndex === index) return;
    setDragOverIndex(index);
  }

  // 拖拽离开
  function handleDragLeave() {
    setDragOverIndex(null);
  }

  // 放置
  function handleDrop(e, dropIndex) {
    e.preventDefault();
    
    if (draggedIndex === null || draggedIndex === dropIndex) {
      setDraggedIndex(null);
      setDragOverIndex(null);
      return;
    }

    const updated = [...games];
    const draggedItem = updated[draggedIndex];
    
    // 移除拖拽项
    updated.splice(draggedIndex, 1);
    // 插入到新位置
    updated.splice(dropIndex, 0, draggedItem);
    
    setGames(updated);
    
    // 更新选中索引
    if (selectedIndex === draggedIndex) {
      setSelectedIndex(dropIndex);
    } else if (selectedIndex !== null) {
      if (draggedIndex < selectedIndex && dropIndex >= selectedIndex) {
        setSelectedIndex(selectedIndex - 1);
      } else if (draggedIndex > selectedIndex && dropIndex <= selectedIndex) {
        setSelectedIndex(selectedIndex + 1);
      }
    }
    
    setDraggedIndex(null);
    setDragOverIndex(null);
    showToast('顺序已调整', 'success');
  }

  // 拖拽结束
  function handleDragEnd() {
    setDraggedIndex(null);
    setDragOverIndex(null);
  }

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-5xl h-[80vh] shadow-2xl flex flex-col overflow-hidden">
        
        {/* 弹窗头部 */}
        <header className="flex-none flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-gradient-to-r from-slate-50 to-white">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-indigo-50 rounded-lg">
              <Settings className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-800">配置管理</h2>
              <p className="text-xs text-slate-400">管理游戏监控配置</p>
            </div>
          </div>
          <button 
            onClick={() => onClose(games)}
            className="p-2 hover:bg-slate-100 rounded-lg transition-colors text-slate-400 hover:text-slate-600"
          >
            <X className="w-5 h-5" />
          </button>
        </header>

        {/* 主内容区 */}
        <div className="flex-1 flex overflow-hidden">
          
          {/* 左侧：游戏列表 */}
          <aside className="flex-none w-80 border-r border-slate-200 bg-slate-50 flex flex-col">
            <div className="flex-none p-4 border-b border-slate-200 bg-white">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-slate-700">游戏列表</h3>
                <span className="text-xs text-slate-400 bg-slate-100 px-2 py-0.5 rounded-full">
                  {games.length} 个
                </span>
              </div>
              <button
                onClick={handleNew}
                className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
              >
                <Plus className="w-4 h-4" />
                新增游戏
              </button>
            </div>
            
            <div className="flex-1 overflow-y-auto p-4 space-y-2">
              {games.length === 0 ? (
                <div className="text-center py-12 text-slate-400">
                  <Gamepad2 className="w-12 h-12 mx-auto mb-3 opacity-20" />
                  <p className="text-sm">暂无游戏配置</p>
                  <p className="text-xs mt-1">点击"新增游戏"开始</p>
                </div>
              ) : (
                games.map((game, idx) => (
                  <div
                    key={idx}
                    draggable
                    onDragStart={() => handleDragStart(idx)}
                    onDragOver={(e) => handleDragOver(e, idx)}
                    onDragLeave={handleDragLeave}
                    onDrop={(e) => handleDrop(e, idx)}
                    onDragEnd={handleDragEnd}
                    className={`rounded-lg border transition-all cursor-move ${
                      draggedIndex === idx
                        ? 'opacity-50 scale-95'
                        : dragOverIndex === idx
                        ? 'border-indigo-400 bg-indigo-50 shadow-lg scale-105'
                        : selectedIndex === idx
                        ? 'bg-indigo-50 border-indigo-200 ring-2 ring-indigo-100'
                        : 'bg-white border-slate-200 hover:border-indigo-200 hover:shadow-sm'
                    }`}
                  >
                    <button
                      onClick={() => handleEdit(idx)}
                      className="w-full text-left p-3"
                    >
                      <div className="flex items-center gap-3 mb-2">
                        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-slate-100 to-slate-200 flex items-center justify-center text-sm font-bold text-slate-600">
                          {game.name[0]}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="text-sm font-bold text-slate-800 truncate">{game.name}</h4>
                          <p className="text-xs text-slate-400 truncate">ID: {game.id}</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                          game.enabled 
                            ? 'bg-emerald-100 text-emerald-600' 
                            : 'bg-slate-100 text-slate-400'
                        }`}>
                          {game.enabled ? '已启用' : '已禁用'}
                        </span>
                        <span className="text-[10px] text-slate-400">{game.created_at}</span>
                      </div>
                    </button>
                  </div>
                ))
              )}
            </div>
          </aside>

          {/* 右侧：编辑表单 */}
          <main className="flex-1 flex flex-col overflow-hidden">
            {editMode ? (
              <>
                <div className="flex-1 overflow-y-auto p-6">
                  <div className="max-w-2xl mx-auto space-y-6">
                    
                    {/* 基础信息 */}
                    <section>
                      <h3 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <div className="w-1 h-4 bg-indigo-500 rounded-full"></div>
                        基础信息
                      </h3>
                      
                      <div className="space-y-4">
                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">
                            游戏 ID <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.id}
                            onChange={(e) => handleFieldChange('id', e.target.value)}
                            placeholder="例如: naraka"
                            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-all ${
                              errors.id 
                                ? 'border-red-300 focus:ring-red-200' 
                                : 'border-slate-300 focus:ring-indigo-200'
                            }`}
                          />
                          {errors.id && (
                            <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" />
                              {errors.id}
                            </p>
                          )}
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">
                            游戏名称 <span className="text-red-500">*</span>
                          </label>
                          <input
                            type="text"
                            value={formData.name}
                            onChange={(e) => handleFieldChange('name', e.target.value)}
                            placeholder="例如: 永劫无间"
                            className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-all ${
                              errors.name 
                                ? 'border-red-300 focus:ring-red-200' 
                                : 'border-slate-300 focus:ring-indigo-200'
                            }`}
                          />
                          {errors.name && (
                            <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                              <AlertCircle className="w-3 h-3" />
                              {errors.name}
                            </p>
                          )}
                        </div>

                        <div>
                          <label className="block text-xs font-medium text-slate-600 mb-1.5">
                            图标 URL（选填）
                          </label>
                          <input
                            type="text"
                            value={formData.icon_url}
                            onChange={(e) => handleFieldChange('icon_url', e.target.value)}
                            placeholder="https://example.com/icon.png"
                            className="w-full px-3 py-2 border border-slate-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-indigo-200 transition-all"
                          />
                          <p className="text-xs text-slate-400 mt-1">不填则显示游戏名首字符</p>
                        </div>

                        <div className="flex items-center justify-between p-3 bg-slate-50 rounded-lg border border-slate-200">
                          <div>
                            <p className="text-sm font-medium text-slate-700">启用监控</p>
                            <p className="text-xs text-slate-400">禁用后将不会爬取该游戏数据</p>
                          </div>
                          <button
                            onClick={() => handleFieldChange('enabled', !formData.enabled)}
                            className={`relative w-12 h-6 rounded-full transition-colors ${
                              formData.enabled ? 'bg-emerald-500' : 'bg-slate-300'
                            }`}
                          >
                            <div className={`absolute top-1 w-4 h-4 bg-white rounded-full shadow-md transition-transform ${
                              formData.enabled ? 'translate-x-7' : 'translate-x-1'
                            }`}></div>
                          </button>
                        </div>
                      </div>
                    </section>

                    {/* 平台链接 */}
                    <section>
                      <h3 className="text-sm font-bold text-slate-700 mb-3 flex items-center gap-2">
                        <div className="w-1 h-4 bg-indigo-500 rounded-full"></div>
                        平台链接
                      </h3>
                      
                      <div className="space-y-4">
                        {[
                          { key: 'taptap', label: 'TapTap', placeholder: 'https://www.taptap.cn/app/123456' },
                          { key: 'bilibili', label: 'B站', placeholder: 'https://www.bilibili.com/game/123' },
                          { key: 'weibo', label: '微博', placeholder: 'https://weibo.com/u/123456' },
                          { key: 'xiaohongshu', label: '小红书', placeholder: 'https://www.xiaohongshu.com/user/profile/xxx' }
                        ].map(platform => (
                          <div key={platform.key}>
                            <label className="block text-xs font-medium text-slate-600 mb-1.5">
                              {platform.label}
                            </label>
                            <input
                              type="text"
                              value={formData.platforms[platform.key].url}
                              onChange={(e) => handlePlatformChange(platform.key, e.target.value)}
                              placeholder={platform.placeholder}
                              className={`w-full px-3 py-2 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-all ${
                                errors[platform.key]
                                  ? 'border-red-300 focus:ring-red-200'
                                  : 'border-slate-300 focus:ring-indigo-200'
                              }`}
                            />
                            {errors[platform.key] && (
                              <p className="text-xs text-red-500 mt-1 flex items-center gap-1">
                                <AlertCircle className="w-3 h-3" />
                                {errors[platform.key]}
                              </p>
                            )}
                          </div>
                        ))}
                      </div>
                    </section>

                  </div>
                </div>

                {/* 表单底部操作栏 */}
                <footer className="flex-none border-t border-slate-200 p-4 bg-slate-50 flex items-center justify-between">
                  <div>
                    {editMode === 'edit' && (
                      <button
                        onClick={handleDelete}
                        className="flex items-center gap-2 px-4 py-2 text-red-600 hover:bg-red-50 rounded-lg text-sm font-medium transition-colors"
                      >
                        <Trash2 className="w-4 h-4" />
                        删除游戏
                      </button>
                    )}
                  </div>
                  <div className="flex gap-3">
                    <button
                      onClick={handleCancel}
                      className="px-4 py-2 text-slate-600 hover:bg-slate-100 rounded-lg text-sm font-medium transition-colors"
                    >
                      取消
                    </button>
                    <button
                      onClick={handleSave}
                      className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
                    >
                      <Save className="w-4 h-4" />
                      保存
                    </button>
                  </div>
                </footer>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center text-slate-400">
                <div className="text-center">
                  <Settings className="w-16 h-16 mx-auto mb-4 opacity-20" />
                  <p className="text-sm font-medium">请选择或新增一个游戏</p>
                  <p className="text-xs mt-1">在左侧列表中选择游戏进行编辑</p>
                </div>
              </div>
            )}
          </main>

        </div>

        {/* 底部工具栏 */}
        <footer className="flex-none border-t border-slate-200 px-6 py-4 bg-white flex items-center justify-between">
          <div className="flex gap-3">
            <button
              onClick={handleImport}
              className="flex items-center gap-2 px-4 py-2 border border-slate-300 hover:bg-slate-50 rounded-lg text-sm font-medium transition-colors text-slate-600"
            >
              <Upload className="w-4 h-4" />
              导入配置
            </button>
            <button
              onClick={handleExport}
              className="flex items-center gap-2 px-4 py-2 border border-slate-300 hover:bg-slate-50 rounded-lg text-sm font-medium transition-colors text-slate-600"
            >
              <Download className="w-4 h-4" />
              导出配置
            </button>
          </div>
          <button
            onClick={handleConfirm}
            className="flex items-center gap-2 px-6 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors shadow-sm"
          >
            <CheckCircle className="w-4 h-4" />
            完成
          </button>
          
          {/* 隐藏的文件输入 */}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            onChange={handleFileChange}
            className="hidden"
          />
        </footer>

        {/* Toast 提示 */}
        {toast && (
          <div className="fixed bottom-6 right-6 z-50 animate-in slide-in-from-bottom-5 duration-300">
            <div className={`flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg ${
              toast.type === 'success' 
                ? 'bg-emerald-500 text-white' 
                : 'bg-red-500 text-white'
            }`}>
              {toast.type === 'success' ? (
                <CheckCircle className="w-5 h-5" />
              ) : (
                <AlertCircle className="w-5 h-5" />
              )}
              <p className="text-sm font-medium">{toast.message}</p>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
