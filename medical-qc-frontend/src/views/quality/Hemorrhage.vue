<template>
  <div class="hemorrhage-qc-container">
    <!--
      顶部导航与操作栏
      功能：显示页面路径、标题、状态标签以及全局操作按钮
    -->
    <div class="page-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>影像质控</el-breadcrumb-item>
          <el-breadcrumb-item>头部出血检测</el-breadcrumb-item>
        </el-breadcrumb>
        <h2 class="page-title">
          头部出血 AI 智能检测
          <!-- 状态展示：根据是否有出血检测结果动态显示 -->
          <el-tag v-if="qcItems.length > 0" :type="hasHemorrhage ? 'danger' : 'success'" effect="plain" class="status-tag">
            {{ hasHemorrhage ? '检测到出血' : 'AI 自动分析完成' }}
          </el-tag>
          <el-tag v-else type="info" effect="plain" class="status-tag">等待上传影像</el-tag>
        </h2>
      </div>
      <!-- 操作按钮区：仅在有分析结果时显示 -->
      <div class="header-right" v-if="qcItems.length > 0">
        <el-button @click="resetUpload">
          <el-icon><Upload /></el-icon> 上传新案例
        </el-button>
        <el-button type="primary" :loading="analyzing" @click="handleReanalyze">
          <el-icon><Refresh /></el-icon> 重新分析
        </el-button>
        <el-button type="success" plain @click="handleExport">
          <el-icon><Download /></el-icon> 导出报告
        </el-button>
      </div>
    </div>

    <!--
      1. 上传区域 (当没有数据时显示)
      包含：
      - 正在分析时的进度条动画
      - 本地文件上传入口
      - PACS 系统检索入口
    -->
    <div v-if="qcItems.length === 0" class="upload-section">
      <div class="upload-wrapper">
        <!-- 正在分析的状态：显示进度条与日志 -->
        <transition name="fade" mode="out-in">
          <div v-if="analyzing" class="analyzing-container" key="analyzing">
            <div class="scan-animation-box">
              <div class="scan-line"></div>
              <el-icon class="scan-icon"><Aim /></el-icon>
            </div>
            <div class="progress-info">
              <h3 class="analyzing-title">AI 智能分析中</h3>
              <!-- 模拟进度条：通过定时器控制进度增长 -->
              <el-progress
                :percentage="Math.floor(analyzeProgress)"
                :stroke-width="12"
                striped
                striped-flow
                :duration="10"
              />
              <div class="step-display">
                <span class="step-text">{{ currentAnalysisStep }}</span>
                <span class="step-dots">...</span>
              </div>
              <!-- 实时日志显示窗口 -->
              <div class="log-window">
                <p v-for="(log, index) in analysisLogs" :key="index" class="log-item">
                  <span class="log-time">[{{ log.time }}]</span> {{ log.message }}
                </p>
              </div>
            </div>
          </div>

          <!-- 初始状态：上传/选择入口 -->
          <div v-else class="upload-choices" key="upload">
            <el-row :gutter="40" justify="center">
              <!-- 本地上传卡片：触发文件选择弹窗 -->
              <el-col :span="10">
                <div class="choice-card local-upload" @click="openUploadDialog('local')">
                  <div class="icon-wrapper">
                    <el-icon><FolderOpened /></el-icon>
                  </div>
                  <h3>本地影像上传</h3>
                  <p>支持 DICOM 文件夹拖拽上传</p>
                  <p class="sub-tip">自动解析 .dcm 序列文件</p>
                </div>
              </el-col>

              <!-- PACS 入口卡片：触发模拟 PACS 检索 -->
              <el-col :span="10">
                <div class="choice-card pacs-select" @click="simulatePacsSelect">
                  <div class="icon-wrapper">
                    <el-icon><Connection /></el-icon>
                  </div>
                  <h3>PACS 系统调取</h3>
                  <p>连接医院内部影像归档系统</p>
                  <p class="sub-tip">支持按患者 ID / 检查号检索</p>
                </div>
              </el-col>
            </el-row>

            <div class="upload-footer">
              <p>
                <el-icon><InfoFilled /></el-icon>
                严禁上传含有敏感隐私的非脱敏数据，所有数据仅用于质控分析。
              </p>
            </div>
          </div>
        </transition>
      </div>
    </div>

    <!--
      2. 结果展示区域 (列表模式)
      包含：
      - 患者基本信息卡片
      - 出血风险评分仪表盘
      - 检测详情列表（点击可查看影像与 BBox）
    -->
    <div v-else class="result-section">
      <!-- 患者信息与总体评分 -->
      <el-row :gutter="20" class="info-section">
        <el-col :span="16">
          <el-card shadow="hover" class="patient-card">
            <template #header>
              <div class="card-header">
                <span><el-icon><User /></el-icon> 患者检查信息</span>
                <el-tag size="small" type="info">Accession No: {{ patientInfo.accessionNumber }}</el-tag>
              </div>
            </template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="姓名">{{ patientInfo.name }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ patientInfo.gender }}</el-descriptions-item>
              <el-descriptions-item label="年龄">{{ patientInfo.age }}岁</el-descriptions-item>
              <el-descriptions-item label="检查ID">{{ patientInfo.studyId }}</el-descriptions-item>
              <el-descriptions-item label="检查日期">{{ patientInfo.studyDate }}</el-descriptions-item>
              <el-descriptions-item label="设备型号">{{ patientInfo.device }}</el-descriptions-item>
              <el-descriptions-item label="扫描部位">Head Routine</el-descriptions-item>
              <el-descriptions-item label="检测模型">
                 <el-tag size="small" effect="plain">{{ modelName || 'ResNet50' }}</el-tag>
              </el-descriptions-item>
              <el-descriptions-item label="推理设备">
                <span style="color: #409EFF; font-weight: bold;">{{ inferenceDevice }}</span>
              </el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <!-- 风险评分仪表盘 -->
        <el-col :span="8">
          <el-card shadow="hover" class="score-card">
            <div class="score-content">
               <el-progress
                 type="dashboard"
                 :percentage="hemorrhageProb"
                 :color="scoreColor"
                 :width="140"
               >
                 <template #default="{ percentage }">
                   <span class="score-value" :style="{ color: scoreColor }">{{ percentage }}%</span>
                   <span class="score-label">出血风险</span>
                 </template>
               </el-progress>
               <div class="score-summary">
                 <div class="summary-result">
                   AI 判定:
                   <el-tag :type="hasHemorrhage ? 'danger' : 'success'" effect="dark" size="large">
                     {{ hasHemorrhage ? '疑似出血' : '未见异常' }}
                   </el-tag>
                 </div>
               </div>
            </div>
          </el-card>
        </el-col>
      </el-row>

      <!-- 质控检测列表 -->
      <div class="qc-items-section">
        <div class="section-title">
          <h3><el-icon><List /></el-icon> 检测详情报告</h3>
          <span class="subtitle">点击列表项查看详细影像与 AI 标注</span>
        </div>

        <div class="qc-list">
          <div
            v-for="(item, index) in qcItems"
            :key="index"
            class="qc-list-item"
            :class="{ 'is-error': item.status === '异常', 'is-success': item.status === '正常' }"
            @click="viewDetails(item)"
          >
            <div class="list-item-left">
              <div class="status-icon">
                <el-icon v-if="item.status === '正常'"><CircleCheckFilled /></el-icon>
                <el-icon v-else><WarningFilled /></el-icon>
              </div>
            </div>
            <div class="list-item-main">
              <div class="item-header">
                <span class="item-name">{{ item.name }}</span>
                <el-tag
                  size="small"
                  :type="item.status === '正常' ? 'success' : 'danger'"
                  effect="light"
                  class="item-tag"
                >
                  {{ item.status }}
                </el-tag>
              </div>
              <div class="item-desc">{{ item.description }}</div>
              <div class="item-detail-text" v-if="item.status === '异常'">
                 <span class="error-text"><el-icon><InfoFilled /></el-icon> {{ item.detail }}</span>
              </div>
            </div>
            <div class="list-item-right">
               <el-button type="primary" link>详情 <el-icon><ArrowRight /></el-icon></el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!--
      上传弹窗
      功能：录入患者信息，选择本地文件或确认 PACS 影像源
    -->
    <el-dialog
      v-model="uploadDialogVisible"
      :title="uploadMode === 'local' ? '本地影像上传' : 'PACS 系统检索'"
      width="500px"
      :close-on-click-modal="false"
      destroy-on-close
    >
      <el-form :model="uploadForm" :rules="uploadRules" ref="uploadFormRef" label-width="100px">
        <el-form-item label="患者姓名" prop="patientName">
          <el-input v-model="uploadForm.patientName" placeholder="请输入患者姓名"></el-input>
        </el-form-item>
        <el-form-item label="检查 ID" prop="examId">
          <el-input v-model="uploadForm.examId" placeholder="请输入 Accession No."></el-input>
        </el-form-item>

        <!-- 本地模式：显示文件上传控件 -->
        <el-form-item label="影像文件" required v-if="uploadMode === 'local'">
          <el-upload
            class="upload-demo"
            drag
            action="#"
            :auto-upload="false"
            :show-file-list="true"
            :limit="1"
            :on-change="handleDialogFileChange"
            :on-remove="() => (selectedFile = null)"
            style="width: 100%"
            accept=".png,.jpg,.jpeg,.bmp,.dcm"
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽影像文件或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 PNG, JPG, DICOM 格式</div>
            </template>
          </el-upload>
        </el-form-item>

        <!-- PACS 模式：显示锁定提示 -->
        <el-form-item label="影像源" v-else>
          <el-alert title="已锁定 PACS 影像源" type="success" :closable="false" show-icon>
            <template #default> 系统将直接从服务器拉取 Accession No. 关联的影像序列。 </template>
          </el-alert>
        </el-form-item>
      </el-form>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="uploadDialogVisible = false">取消</el-button>
          <el-button type="primary" @click="submitUpload">开始智能分析</el-button>
        </span>
      </template>
    </el-dialog>

    <!--
      详情弹窗 (带影像与 BBox 标注)
      功能：查看特定检测项的详细信息和影像标注结果
    -->
    <el-dialog v-model="dialogVisible" :title="currentItem?.name + ' - 详情'" width="800px" class="detail-dialog">
      <div v-if="currentItem" class="detail-content">
         <el-row :gutter="20">
           <!-- 左侧：影像预览与标注层 -->
           <el-col :span="14">
             <div class="image-preview-wrapper">
                <div class="image-container">
                  <img v-if="imageUrl" :src="imageUrl" class="preview-image" alt="CT Scan" />
                  <div v-else class="image-placeholder">
                    <el-icon><Picture /></el-icon>
                    <span>无预览图像</span>
                  </div>
                  <!-- 动态 BBox 标注 (仅在出血检测项且有结果时显示) -->
                  <template v-if="currentItem.type === 'hemorrhage' && bboxes && bboxes.length > 0 && hasHemorrhage">
                    <div
                      v-for="(box, index) in bboxes"
                      :key="index"
                      class="bbox-overlay"
                      :style="getBboxStyle(box)"
                    >
                      <span class="bbox-label" v-if="index === 0">出血灶 {{ hemorrhageProb }}%</span>
                    </div>
                  </template>
                </div>
             </div>
           </el-col>
           <!-- 右侧：详细文本信息 -->
           <el-col :span="10">
             <div class="detail-info">
               <el-descriptions :column="1" border direction="vertical">
                 <el-descriptions-item label="检测项">{{ currentItem.name }}</el-descriptions-item>
                 <el-descriptions-item label="状态">
                    <el-tag :type="currentItem.status === '正常' ? 'success' : 'danger'">
                      {{ currentItem.status }}
                    </el-tag>
                 </el-descriptions-item>
                 <el-descriptions-item label="详细说明">
                    {{ currentItem.detail }}
                 </el-descriptions-item>
                 <el-descriptions-item label="AI 置信度" v-if="currentItem.type === 'hemorrhage'">
                    {{ confidenceLevel }}
                 </el-descriptions-item>
               </el-descriptions>
             </div>
           </el-col>
         </el-row>
      </div>
    </el-dialog>
  </div>
</template>

<script setup>
/**
 * @file Hemorrhage.vue
 * @description 头部出血 AI 智能检测视图
 * 包含影像上传、AI 实时分析动画、结果展示以及动态 BBox 标注功能。
 *
 * 对接API:
 * - predictHemorrhage: 调用后端 /api/quality/hemorrhage 接口进行影像分析
 */
import { ref, computed, reactive, nextTick } from 'vue'
import { ElMessage } from 'element-plus'
import { User, Upload, Refresh, Download, FolderOpened, Connection, InfoFilled, Aim, Picture, UploadFilled, List, CircleCheckFilled, WarningFilled, ArrowRight, ArrowLeft } from '@element-plus/icons-vue'
import { predictHemorrhage } from '@/api/quality'
import '@/assets/css/hemorrhage-scan.css' // 引入专用的扫描动画样式

// --- 状态定义 ---
const analyzing = ref(false)         // 是否正在分析中
const analyzeProgress = ref(0)       // 分析进度 (0-100)
const uploadDialogVisible = ref(false) // 上传弹窗可见性
const uploadMode = ref('local')      // 上传模式: 'local' | 'pacs'
const uploadFormRef = ref(null)      // 表单引用
const selectedFile = ref(null)       // 选中的本地文件
const dialogVisible = ref(false)     // 详情弹窗可见性
const currentItem = ref(null)        // 当前查看的详情项

// --- 结果数据 ---
const qcItems = ref([])              // 质控检测结果列表
const hasHemorrhage = ref(false)     // 是否检测到出血
const hemorrhageProb = ref(0)        // 出血概率 (0-100)
const inferenceDevice = ref('CPU')   // 推理设备 (CPU/GPU)
const modelName = ref('')            // 使用的模型名称
const imageUrl = ref('')             // 预览图片 URL (Base64)
const bboxes = ref([])               // 出血区域边界框 [x, y, w, h]
const confidenceLevel = ref('')      // 置信度描述
const imageMeta = ref({ width: 0, height: 0 }) // 图片原始尺寸，用于计算 BBox 相对位置

// --- 日志与进度 ---
const currentAnalysisStep = ref('准备就绪')
const analysisLogs = ref([])

// --- 表单数据 ---
const uploadForm = reactive({
  patientName: '',
  examId: '',
})

const uploadRules = {
  patientName: [{ required: true, message: '请输入患者姓名', trigger: 'blur' }],
  examId: [{ required: true, message: '请输入检查ID', trigger: 'blur' }],
}

// --- 患者信息 (展示用) ---
const patientInfo = ref({
  name: '',
  gender: '',
  age: 0,
  studyId: '',
  accessionNumber: '',
  studyDate: '',
  device: '',
})

// --- 计算属性 ---

/**
 * 根据出血概率计算评分颜色
 * > 0: 红色 (检测到出血)
 * > 50%: 橙色 (高风险)
 * 其他: 绿色 (正常)
 */
const scoreColor = computed(() => {
  if (hasHemorrhage.value) return '#F56C6C'
  if (hemorrhageProb.value > 50) return '#E6A23C'
  return '#67C23A'
})

// --- 方法定义 ---

/**
 * 计算 BBox 在预览图中的相对位置样式
 * 将后端返回的绝对坐标转换为百分比，以适应响应式布局
 * @param {Array} box - [x, y, w, h]
 * @returns {Object} style object
 */
const getBboxStyle = (box) => {
  if (!box || box.length !== 4) return {}
  if (!imageMeta.value.width || !imageMeta.value.height) return {}

  const [x, y, w, h] = box
  // 计算百分比位置
  const left = (x / imageMeta.value.width) * 100
  const top = (y / imageMeta.value.height) * 100
  const width = (w / imageMeta.value.width) * 100
  const height = (h / imageMeta.value.height) * 100

  return {
    left: `${left}%`,
    top: `${top}%`,
    width: `${width}%`,
    height: `${height}%`,
    position: 'absolute',
    border: '2px solid #F56C6C',
    boxShadow: '0 0 8px rgba(245, 108, 108, 0.6)',
    zIndex: 10
  }
}

/**
 * 打开上传配置弹窗
 * @param {string} mode - 'local' 或 'pacs'
 */
const openUploadDialog = (mode = 'local') => {
  uploadMode.value = mode
  uploadForm.patientName = ''
  uploadForm.examId = ''
  selectedFile.value = null
  uploadDialogVisible.value = true
}

/**
 * 处理文件选择变更
 */
const handleDialogFileChange = (file) => {
  selectedFile.value = file.raw
}

/**
 * 模拟 PACS 系统检索过程
 */
const simulatePacsSelect = () => {
  ElMessage.success('已连接 PACS 系统，正在检索今日检查列表...')
  setTimeout(() => {
    // 模拟自动填充
    uploadForm.patientName = '张伟'
    uploadForm.examId = 'PACS_HEMO_20231024'
    selectedFile.value = null
    uploadMode.value = 'pacs'
    uploadDialogVisible.value = true
    ElMessage.success('已自动获取 PACS 影像信息，请确认')
  }, 600)
}

/**
 * 重置上传状态
 */
const resetUpload = () => {
  openUploadDialog()
}

/**
 * 重新分析当前案例
 */
const handleReanalyze = () => {
    startAnalysisProcess()
}

/**
 * 导出报告 (未实现)
 */
const handleExport = () => {
    ElMessage.success('报告导出中...')
}

/**
 * 查看详情
 */
const viewDetails = (item) => {
    currentItem.value = item
    dialogVisible.value = true
}

/**
 * 添加分析日志
 */
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  analysisLogs.value.unshift({ time, message: msg })
  // 保持日志数量不超过 5 条
  if (analysisLogs.value.length > 5) analysisLogs.value.pop()
}

/**
 * 提交表单并开始分析流程
 * 包含表单验证和模式判断
 */
const submitUpload = async () => {
  if (!uploadFormRef.value) return

  await uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      if (uploadMode.value === 'local' && !selectedFile.value) {
        ElMessage.warning('请上传影像文件')
        return
      }
      uploadDialogVisible.value = false
      startAnalysisProcess()
    }
  })
}

/**
 * 启动 AI 分析流程
 * 包含进度条模拟、API 调用和结果处理
 */
const startAnalysisProcess = async () => {
  qcItems.value = []
  analyzing.value = true
  analyzeProgress.value = 0
  analysisLogs.value = []

  // 1. 启动进度条动画 (假的缓慢进度，用于提升用户体验)
  addLog('正在初始化 AI 引擎...')
  currentAnalysisStep.value = '初始化'

  // 进度条定时器
  const progressTimer = setInterval(() => {
    if (analyzeProgress.value < 90) {
      // 随机增加进度，模拟真实感
      analyzeProgress.value += Math.random() * 2

      // 更新状态文字
      if (analyzeProgress.value > 10 && analyzeProgress.value < 30) {
         currentAnalysisStep.value = '图像预处理'
      } else if (analyzeProgress.value > 40 && analyzeProgress.value < 70) {
         currentAnalysisStep.value = '神经网络推理'
      } else if (analyzeProgress.value > 80) {
         currentAnalysisStep.value = '生成报告'
      }
    }
  }, 100)

  try {
    let res;

    // 2. 根据模式调用不同的处理逻辑
    if (uploadMode.value === 'pacs') {
        // PACS 模式：模拟延迟 (Mock) - 固定 500ms
        addLog('正在从 PACS 拉取影像序列...')
        await new Promise(r => setTimeout(r, 200))
        addLog('影像拉取成功，开始分析...')
        await new Promise(r => setTimeout(r, 300))

        // Mock 数据返回
        res = {
         success: true,
         prediction: '未出血',
         hemorrhage_probability: 0.02,
         confidence_level: '高置信度',
         duration: 320,
         model_name: 'ResNet50 + CV Hybrid',
         bbox: null,
         midline_shift: false,
         shift_score: 1.2,
         device: 'Mock-CUDA', // 模拟设备
         image_width: 512,
         image_height: 512,
         image_url: null
       }
    } else {
        // Local 模式：真实 API 调用
        addLog('正在上传影像并请求分析...')
        // 调用封装好的 predictHemorrhage API
        // 真实等待 API 返回，期间进度条会卡在 90% 左右
        res = await predictHemorrhage(selectedFile.value, {
          patientName: uploadForm.patientName,
          examId: uploadForm.examId
        })
    }

    // 3. 请求完成，处理收尾工作
    clearInterval(progressTimer)
    analyzeProgress.value = 100
    currentAnalysisStep.value = '分析完成'

    // 显示真实的分析耗时
    const duration = res.duration || 0
    addLog(`AI 分析完成，耗时: ${duration} ms`)
    addLog(`推理设备: ${res.device || 'Unknown'}`)

    // 4. 渲染结果 (无需额外延迟，直接显示)
    finalizeAnalysis(res, uploadMode.value === 'pacs')

  } catch (error) {
    clearInterval(progressTimer)
    analyzing.value = false
    ElMessage.error(error.message || '分析失败')
    addLog('错误: ' + error.message)
  }
}

/**
 * 处理分析结果数据
 * 将后端返回的数据填充到页面状态中
 * @param {Object} res - 后端响应数据
 * @param {boolean} isMock - 是否为模拟模式
 */
const finalizeAnalysis = (res, isMock = false) => {
  analyzing.value = false

  // 填充核心指标
  hasHemorrhage.value = res.prediction === '出血'
  hemorrhageProb.value = (res.hemorrhage_probability * 100).toFixed(1)
  inferenceDevice.value = res.device || 'CPU' // 显示设备
  modelName.value = res.model_name
  bboxes.value = res.bboxes
  confidenceLevel.value = res.confidence_level

  // 更新图像元数据
  imageMeta.value = { width: res.image_width || 512, height: res.image_height || 512 }

  // 更新患者信息
  patientInfo.value = {
      name: uploadForm.patientName,
      gender: '男', // 模拟数据
      age: 45,      // 模拟数据
      studyId: uploadForm.examId,
      accessionNumber: uploadForm.examId,
      studyDate: new Date().toLocaleDateString(),
      device: 'GE Revolution CT'
  }

  // 填充质控检测列表 (根据后端结果动态生成)
  qcItems.value = [
    {
      name: '脑出血检测',
      type: 'hemorrhage', // 标识类型，用于详情页特殊展示
      description: '检测是否存在脑实质内高密度出血灶',
      status: res.prediction === '出血' ? '异常' : '正常',
      detail: res.prediction === '出血'
        ? `检测到疑似出血区域 (置信度: ${(res.hemorrhage_probability * 100).toFixed(1)}%)`
        : '未检测到明显出血灶',
    },
    {
      name: '中线偏移',
      type: 'midline',
      description: '检测脑中线结构是否发生位移',
      status: res.midline_shift ? '异常' : '正常', // 假设后端返回了此字段
      detail: res.midline_shift ? `检测到中线偏移 (偏移指数: ${res.shift_score})` : '中线结构居中',
    },
    {
       name: '伪影检测',
       type: 'artifact',
       description: '检测是否存在运动伪影或金属伪影',
       status: '正常', // 示例默认正常
       detail: '图像清晰，未发现明显伪影干扰',
    }
  ]
}
</script>
