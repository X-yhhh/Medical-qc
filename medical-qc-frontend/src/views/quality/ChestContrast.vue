<!--
  @file src/views/quality/ChestContrast.vue
  @description CT胸部增强智能质控视图
  主要功能：
  1. 影像上传：支持本地DICOM文件夹拖拽上传和PACS系统模拟拉取。
  2. AI智能分析：展示分析进度、当前步骤和实时日志。
  3. 结果展示：
     - 患者检查信息卡片
     - 质控评分仪表盘
     - 异常项汇总
     - 详细质控检测项列表（按扫描时相分组）
  4. 详情查看：点击质控项查看详细分析结果和影像快照（Mock）。

  @api Mocks (模拟后端接口)
  - simulatePacsSelect: 模拟从PACS系统检索影像信息
  - startAnalysisProcess: 模拟长连接/WebSocket推送的分析流程
  - fetchQCData: 模拟获取最终质控报告数据
-->
<template>
  <div class="chest-contrast-qc-container">
    <!--
      @section 顶部导航与操作栏
      包含：面包屑导航、页面标题、状态标签、以及分析完成后的操作按钮（上传、重新分析、导出）
    -->
    <div class="page-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>影像质控</el-breadcrumb-item>
          <el-breadcrumb-item>CT胸部增强</el-breadcrumb-item>
        </el-breadcrumb>
        <h2 class="page-title">
          CT胸部增强智能质控
          <el-tag v-if="qcItems.length > 0" type="primary" effect="plain" class="status-tag"
            >AI 自动分析完成</el-tag
          >
          <el-tag v-else type="info" effect="plain" class="status-tag">等待上传影像</el-tag>
        </h2>
      </div>
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
      @section 上传区域
      当没有质控数据时显示。
      包含：
      1. 分析中的动画状态 (analyzing = true)
      2. 上传方式选择卡片 (本地上传 / PACS调取)
    -->
    <div v-if="qcItems.length === 0" class="upload-section">
      <div class="upload-wrapper">
        <!-- 正在分析的状态 (覆盖在上传区域之上，或者替换它) -->
        <transition name="fade" mode="out-in">
          <div v-if="analyzing" class="analyzing-container" key="analyzing">
            <div class="scan-animation-box">
              <div class="scan-line"></div>
              <el-icon class="scan-icon"><Aim /></el-icon>
            </div>
            <div class="progress-info">
              <h3 class="analyzing-title">AI 智能分析中</h3>
              <el-progress
                :percentage="analyzeProgress"
                :stroke-width="12"
                striped
                striped-flow
                :duration="10"
              />
              <div class="step-display">
                <span class="step-text">{{ currentAnalysisStep }}</span>
                <span class="step-dots">...</span>
              </div>
              <div class="log-window">
                <p v-for="(log, index) in analysisLogs" :key="index" class="log-item">
                  <span class="log-time">[{{ log.time }}]</span> {{ log.message }}
                </p>
              </div>
            </div>
          </div>

          <!-- 上传/选择入口 -->
          <div v-else class="upload-choices" key="upload">
            <el-row :gutter="40" justify="center">
              <!-- 本地上传卡片 -->
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

              <!-- PACS 入口卡片 -->
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
      @section 结果展示区域
      当有质控数据时显示。
      包含：
      1. 患者信息卡片 (Patient Info)
      2. 质控评分仪表盘 (Quality Score)
    -->
    <div v-else class="result-section">
      <!-- 患者信息与总体评分 -->
      <el-row :gutter="20" class="info-section">
        <el-col :span="16">
          <el-card shadow="hover" class="patient-card">
            <template #header>
              <div class="card-header">
                <span
                  ><el-icon><User /></el-icon> 患者检查信息</span
                >
                <el-tag size="small" type="info"
                  >Accession No: {{ patientInfo.accessionNumber }}</el-tag
                >
              </div>
            </template>
            <el-descriptions :column="3" border>
              <el-descriptions-item label="姓名">{{ patientInfo.name }}</el-descriptions-item>
              <el-descriptions-item label="性别">{{ patientInfo.gender }}</el-descriptions-item>
              <el-descriptions-item label="年龄">{{ patientInfo.age }}岁</el-descriptions-item>
              <el-descriptions-item label="检查ID">{{ patientInfo.studyId }}</el-descriptions-item>
              <el-descriptions-item label="检查日期">{{
                patientInfo.studyDate
              }}</el-descriptions-item>
              <el-descriptions-item label="设备型号">{{ patientInfo.device }}</el-descriptions-item>
              <el-descriptions-item label="扫描部位">Chest Contrast</el-descriptions-item>
              <el-descriptions-item label="造影剂流速"
                >{{ patientInfo.flowRate }} mL/s</el-descriptions-item
              >
              <el-descriptions-item label="造影剂总量"
                >{{ patientInfo.contrastVolume }} mL</el-descriptions-item
              >
              <el-descriptions-item label="图像层数"
                >{{ patientInfo.sliceCount }} 层</el-descriptions-item
              >
              <el-descriptions-item label="层厚"
                >{{ patientInfo.sliceThickness }} mm</el-descriptions-item
              >
              <el-descriptions-item label="注射部位">{{
                patientInfo.injectionSite
              }}</el-descriptions-item>
            </el-descriptions>
          </el-card>
        </el-col>
        <el-col :span="8">
          <el-card shadow="hover" class="score-card">
            <div class="score-content">
              <el-progress
                type="dashboard"
                :percentage="qualityScore"
                :color="scoreColor"
                :width="140"
              >
                <template #default="{ percentage }">
                  <span class="score-value">{{ percentage }}</span>
                  <span class="score-label">质控评分</span>
                </template>
              </el-progress>
              <div class="score-summary">
                <div class="summary-item">
                  <span class="label">检测项数</span>
                  <span class="value">{{ qcItems.length }}</span>
                </div>
                <div class="summary-item">
                  <span class="label">异常项</span>
                  <span class="value danger">{{ abnormalCount }}</span>
                </div>
                <div class="summary-result">
                  综合判定:
                  <el-tag :type="qualityScore >= 80 ? 'success' : 'danger'" effect="dark">
                    {{ qualityScore >= 80 ? '合格' : '不合格' }}
                  </el-tag>
                </div>
              </div>
            </div>
          </el-card>
        </el-col>
      </el-row>
    </div>

    <!--
      @section 质控项详情 (分组列表模式)
      按 '定位片', '平扫期', '增强I期', '增强II期' 等分组展示质控项。
    -->
    <div v-if="qcItems.length > 0" class="qc-items-section">
      <div class="section-title">
        <h3>
          <el-icon><List /></el-icon> 质控检测详情
        </h3>
        <span class="subtitle"
          >系统自动检测 {{ qcItems.length }} 项关键指标，请重点关注异常项。</span
        >
      </div>

      <div class="qc-list">
        <!-- 分组渲染 -->
        <div v-for="(group, groupName) in groupedQcItems" :key="groupName" class="qc-group">
          <div class="group-header">
            <span class="group-title">{{ groupName }}</span>
            <el-tag size="small" type="info" effect="plain">{{ group.length }} 项</el-tag>
          </div>

          <div
            v-for="(item, index) in group"
            :key="index"
            class="qc-list-item"
            :class="{ 'is-error': item.status === '不合格', 'is-success': item.status === '合格' }"
            @click="viewDetails(item)"
          >
            <!-- 左侧：图标与状态 -->
            <div class="list-item-left">
              <div class="status-icon">
                <el-icon v-if="item.status === '合格'"><CircleCheckFilled /></el-icon>
                <el-icon v-else><WarningFilled /></el-icon>
              </div>
            </div>

            <!-- 中间：信息主体 -->
            <div class="list-item-main">
              <div class="item-header">
                <span class="item-name">{{ item.name }}</span>
                <el-tag
                  size="small"
                  :type="item.status === '合格' ? 'success' : 'danger'"
                  effect="light"
                  class="item-tag"
                >
                  {{ item.status }}
                </el-tag>
              </div>
              <div class="item-desc">
                {{ item.description }}
              </div>
              <div class="item-detail-text" v-if="item.status === '不合格'">
                <span class="error-text"
                  ><el-icon><InfoFilled /></el-icon> {{ item.detail }}</span
                >
              </div>
            </div>

            <!-- 右侧：操作与分数 (可选) -->
            <div class="list-item-right">
              <el-button type="primary" link @click.stop="viewDetails(item)">
                查看详情 <el-icon class="el-icon--right"><ArrowRight /></el-icon>
              </el-button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!--
      @section 详情弹窗 (Mock)
      展示单项质控指标的详细分析结果。
    -->
    <el-dialog v-model="dialogVisible" :title="currentItem?.name + ' - 详情分析'" width="50%">
      <div v-if="currentItem" class="dialog-content">
        <el-descriptions border :column="1">
          <el-descriptions-item label="检测项">{{ currentItem.name }}</el-descriptions-item>
          <el-descriptions-item label="当前状态">
            <el-tag :type="currentItem.status === '合格' ? 'success' : 'danger'">{{
              currentItem.status
            }}</el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="判定标准">{{
            currentItem.description
          }}</el-descriptions-item>
          <el-descriptions-item label="详细日志">
            {{
              currentItem.status === '合格'
                ? 'AI 算法扫描全序列，未检出异常特征值。'
                : currentItem.detail + '，建议技师检查扫描参数或重新扫描。'
            }}
          </el-descriptions-item>
        </el-descriptions>

        <div class="mock-image-placeholder">
          <el-empty description="此处将显示相关层面的影像快照与AI标注" :image-size="120"></el-empty>
        </div>
      </div>
      <template #footer>
        <span class="dialog-footer">
          <el-button @click="dialogVisible = false">关闭</el-button>
          <el-button type="primary" @click="dialogVisible = false">确认</el-button>
        </span>
      </template>
    </el-dialog>

    <!--
      @section 新建案例弹窗
      用户填写患者信息或确认PACS信息，启动分析流程。
    -->
    <el-dialog v-model="uploadDialogVisible" title="新建质控案例" width="500px" destroy-on-close>
      <el-form
        ref="uploadFormRef"
        :model="uploadForm"
        :rules="uploadRules"
        label-width="100px"
        status-icon
      >
        <el-form-item label="患者姓名" prop="patientName">
          <el-input v-model="uploadForm.patientName" placeholder="请输入患者姓名" />
        </el-form-item>
        <el-form-item label="检查 ID" prop="examId">
          <el-input v-model="uploadForm.examId" placeholder="请输入检查/住院号" />
        </el-form-item>

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
          >
            <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
            <div class="el-upload__text">拖拽 DICOM 文件夹或 <em>点击上传</em></div>
            <template #tip>
              <div class="el-upload__tip">支持 .dcm 序列文件，单次最大 500MB</div>
            </template>
          </el-upload>
        </el-form-item>

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
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, reactive } from 'vue'
import { ElMessage } from 'element-plus'
import { ArrowLeft, User, Upload, Refresh, Download, FolderOpened, Connection, InfoFilled, Aim, Picture, UploadFilled, List, CircleCheckFilled, WarningFilled, ArrowRight } from '@element-plus/icons-vue'

// 模拟状态
const analyzing = ref(false)
const analyzeProgress = ref(0) // 进度条百分比
const dialogVisible = ref(false)
const currentItem = ref(null)

// 新增：上传弹窗相关状态
const uploadDialogVisible = ref(false)
const uploadMode = ref('local') // 'local' | 'pacs'
const uploadFormRef = ref(null)
const uploadForm = reactive({
  patientName: '',
  examId: '',
})
const selectedFile = ref(null)

const uploadRules = {
  patientName: [{ required: true, message: '请输入患者姓名', trigger: 'blur' }],
  examId: [{ required: true, message: '请输入检查ID', trigger: 'blur' }],
}

/**
 * @function openUploadDialog
 * @description 打开上传对话框
 * @param {string} mode - 上传模式 'local' 或 'pacs'
 */
const openUploadDialog = (mode = 'local') => {
  uploadMode.value = mode
  uploadForm.patientName = ''
  uploadForm.examId = ''
  selectedFile.value = null
  uploadDialogVisible.value = true
}

/**
 * @function handleDialogFileChange
 * @description 处理文件选择变更
 * @param {File} file - Element Plus upload 组件返回的文件对象
 */
const handleDialogFileChange = (file) => {
  selectedFile.value = file
}

/**
 * @function submitUpload
 * @description 提交上传表单并触发分析流程
 *
 * 逻辑:
 * 1. 验证表单信息
 * 2. 检查文件是否已选择 (Local 模式)
 * 3. 关闭弹窗并调用 startAnalysisProcess
 */
const submitUpload = async () => {
  if (!uploadFormRef.value) return

  await uploadFormRef.value.validate(async (valid) => {
    if (valid) {
      // 本地上传模式下，必须选择文件
      if (uploadMode.value === 'local' && !selectedFile.value) {
        ElMessage.warning('请上传影像文件')
        return
      }

      // PACS 模式下，不需要文件，因为是后端拉取
      if (uploadMode.value === 'pacs') {
        ElMessage.info(`正在通知后端从 PACS 拉取 ID: ${uploadForm.examId} 的数据...`)
      }

      // 关闭弹窗
      uploadDialogVisible.value = false
      // 开始分析流程
      await startAnalysisProcess()
    }
  })
}

// 分析过程相关状态
const currentAnalysisStep = ref('准备就绪')
const analysisLogs = ref([])

/**
 * @function simulatePacsSelect
 * @description 模拟从 PACS 系统选择病例
 *
 * 逻辑:
 * 1. 模拟网络请求延迟
 * 2. 自动填充患者信息
 * 3. 切换到 PACS 上传模式并打开确认弹窗
 */
const simulatePacsSelect = () => {
  ElMessage.success('已连接 PACS 系统，正在检索今日检查列表...')
  // 模拟从 PACS 获取到数据，弹出对话框让用户确认
  setTimeout(() => {
    uploadForm.patientName = '王某某'
    uploadForm.examId = 'PACS_ENH_20231024'
    // PACS 模式不需要 selectedFile
    selectedFile.value = null

    // 打开弹窗，指定为 pacs 模式
    uploadMode.value = 'pacs'
    uploadDialogVisible.value = true

    ElMessage.success('已自动获取 PACS 影像信息，请确认')
  }, 500)
}

// 模拟患者数据
const patientInfo = ref({
  name: '',
  gender: '',
  age: 0,
  studyId: '',
  accessionNumber: '',
  studyDate: '',
  device: '',
  sliceCount: 0,
  sliceThickness: 0,
  flowRate: 0,
  contrastVolume: 0,
  injectionSite: '',
})

// 质控项数据
const qcItems = ref([])

/**
 * @computed groupedQcItems
 * @description 将质控项按 phase (扫描时相) 分组
 * @returns {Object} 分组后的质控项对象，key 为组名，value 为数组
 */
const groupedQcItems = computed(() => {
  const groups = {
    定位片: [],
    平扫期: [],
    增强I期: [],
    增强II期: [],
  }

  qcItems.value.forEach((item) => {
    if (groups[item.phase]) {
      groups[item.phase].push(item)
    } else {
      // 容错处理
      if (!groups['其他']) groups['其他'] = []
      groups['其他'].push(item)
    }
  })

  // 过滤空组
  const result = {}
  Object.keys(groups).forEach((key) => {
    if (groups[key].length > 0) {
      result[key] = groups[key]
    }
  })
  return result
})

// 重置上传 (改为打开弹窗)
const resetUpload = () => {
  openUploadDialog()
}

/**
 * @function addLog
 * @description 添加分析日志
 * @param {string} msg - 日志消息
 */
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  analysisLogs.value.unshift({ time, message: msg })
  // 保持日志最多 5 条
  if (analysisLogs.value.length > 5) analysisLogs.value.pop()
}

/**
 * @function startAnalysisProcess
 * @description 执行模拟的 AI 分析流程
 *
 * 流程:
 * 1. 初始化状态 (analyzing, progress, logs)
 * 2. 遍历预定义的步骤数组，模拟每一步的耗时
 * 3. 在特定步骤填充模拟的患者信息
 * 4. 完成后调用 fetchQCData 获取结果
 */
const startAnalysisProcess = async () => {
  // 清除旧数据，切换到分析视图
  qcItems.value = []
  patientInfo.value = { name: '' }

  analyzing.value = true
  analyzeProgress.value = 0
  analysisLogs.value = []

  // 模拟分析流程
  const steps = [
    { progress: 10, msg: '正在读取 DICOM 文件头信息...', step: 'DICOM 解析' },
    { progress: 30, msg: '校验序列完整性 (320/320 slices)...', step: '完整性校验' },
    {
      progress: 45,
      msg: `提取患者元数据: ${uploadForm.patientName || '未知'}, ...`,
      step: '元数据提取',
    },
    { progress: 60, msg: 'AI 模型加载中 (Chest_CT_Enh_v1.0)...', step: '模型加载' },
    { progress: 80, msg: '正在分析增强时相与血管充盈度...', step: '特征提取' },
    { progress: 95, msg: '生成结构化质控报告...', step: '报告生成' },
    { progress: 100, msg: '分析完成', step: '完成' },
  ]

  for (const step of steps) {
    await new Promise((resolve) => setTimeout(resolve, 200 + Math.random() * 200))
    analyzeProgress.value = step.progress
    currentAnalysisStep.value = step.step
    addLog(step.msg)

    // 在中间某个时刻填充患者数据
    if (step.progress === 45) {
      // 使用表单数据 + 模拟数据
      patientInfo.value = {
        name: uploadForm.patientName || '自动提取中...',
        gender: Math.random() > 0.5 ? '男' : '女', // 模拟自动获取
        age: 45 + Math.floor(Math.random() * 30), // 模拟自动获取
        studyId: uploadForm.examId || 'UNKNOWN',
        accessionNumber: 'ACC' + Math.floor(Math.random() * 100000), // 模拟自动获取
        studyDate: new Date().toLocaleString(), // 模拟自动获取
        device: 'Siemens Somatom Force', // 模拟自动获取
        sliceCount: 320, // 模拟自动获取
        sliceThickness: 1.0, // 模拟自动获取
        flowRate: 4.5, // 模拟流速
        contrastVolume: 80, // 模拟剂量
        injectionSite: '右侧肘正中静脉', // 模拟注射部位
      }
    }
  }

  await fetchQCData()
}

/**
 * @computed abnormalCount
 * @description 计算不合格的质控项数量
 */
const abnormalCount = computed(() => {
  return qcItems.value.filter((item) => item.status === '不合格').length
})

/**
 * @computed qualityScore
 * @description 计算总体质控评分
 * 算法: 合格项占比 * 100
 */
const qualityScore = computed(() => {
  if (qcItems.value.length === 0) return 0
  const passed = qcItems.value.filter((item) => item.status === '合格').length
  return Math.round((passed / qcItems.value.length) * 100)
})

/**
 * @computed scoreColor
 * @description 根据评分返回颜色值 (绿色/橙色/红色)
 */
const scoreColor = computed(() => {
  if (qualityScore.value >= 90) return '#67C23A'
  if (qualityScore.value >= 60) return '#E6A23C'
  return '#F56C6C'
})

/**
 * @function fetchQCData
 * @description 模拟从后端获取详细质控数据
 *
 * @note 实际项目中应替换为真实 API 调用:
 * const res = await request.get(`/quality/chest-contrast/${taskId}`)
 */
const fetchQCData = async () => {
  analyzing.value = true
  // 模拟网络延迟 (缩短)
  await new Promise((resolve) => setTimeout(resolve, 300))

  // 模拟返回数据 - 增强CT特有
  qcItems.value = [
    {
      name: '定位像范围',
      description: '包含肺尖至肺底完整范围',
      status: '合格',
      phase: '定位片',
      detail: '',
    },
    {
      name: '呼吸配合',
      description: '无明显呼吸运动伪影',
      status: '合格',
      phase: '平扫期',
      detail: '',
    },
    {
      name: '金属伪影',
      description: '无明显金属植入物伪影',
      status: '合格',
      phase: '平扫期',
      detail: '',
    },
    {
      name: '主动脉强化值',
      description: '主动脉弓CT值应 > 250 HU',
      status: '合格',
      phase: '增强I期',
      detail: '实测平均值 320 HU',
    },
    {
      name: '肺动脉强化',
      description: '肺动脉主干CT值应 > 200 HU',
      status: '合格',
      phase: '增强I期',
      detail: '实测平均值 280 HU',
    },
    {
      name: '静脉污染',
      description: '上腔静脉无明显高密度伪影',
      status: '不合格',
      phase: '增强I期',
      detail: '上腔静脉见明显条束状硬化伪影，建议生理盐水冲刷',
    },
    {
      name: '实质强化均匀度',
      description: '肝脏实质强化均匀',
      status: '合格',
      phase: '增强II期',
      detail: '',
    },
  ]
  analyzing.value = false
}

// 详情查看
const viewDetails = (item) => {
  currentItem.value = item
  dialogVisible.value = true
}

// 重新分析
const handleReanalyze = () => {
  ElMessage.info('正在请求云端重新计算...')
  startAnalysisProcess()
}

// 导出报告
const handleExport = () => {
  ElMessage.success('报告下载链接已生成，正在下载...')
}
</script>

<style scoped>
/*
  @section 页面样式
  使用 CSS Grid 和 Flexbox 布局
*/
.chest-contrast-qc-container {
  padding: 20px;
  max-width: 1600px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-title {
  margin-top: 12px;
  margin-bottom: 0;
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  font-weight: normal;
}

/* 上传区域样式 */
.upload-section {
  min-height: 400px;
  display: flex;
  justify-content: center;
  align-items: center;
  background: #f5f7fa;
  border-radius: 8px;
  border: 2px dashed #dcdfe6;
}

.upload-wrapper {
  width: 100%;
  max-width: 800px;
  text-align: center;
}

/* 分析中状态 */
.analyzing-container {
  padding: 40px;
}

.scan-animation-box {
  width: 120px;
  height: 120px;
  background: #2b3b4e;
  border-radius: 50%;
  margin: 0 auto 24px;
  position: relative;
  display: flex;
  justify-content: center;
  align-items: center;
  overflow: hidden;
  box-shadow: 0 0 20px rgba(64, 158, 255, 0.3);
}

.scan-icon {
  font-size: 48px;
  color: #409eff;
  z-index: 2;
}

.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(90deg, transparent, #00ffcc, transparent);
  animation: scan 1.5s infinite linear;
  z-index: 1;
}

@keyframes scan {
  0% {
    top: 0%;
  }
  100% {
    top: 100%;
  }
}

.analyzing-title {
  font-size: 20px;
  color: #303133;
  margin-bottom: 16px;
}

.step-display {
  margin-top: 12px;
  color: #606266;
  font-size: 14px;
}

.log-window {
  margin-top: 24px;
  background: #1e1e1e;
  color: #67c23a;
  padding: 12px;
  border-radius: 4px;
  font-family: 'Consolas', monospace;
  text-align: left;
  height: 120px;
  overflow: hidden;
  font-size: 12px;
}

.log-item {
  margin: 4px 0;
  opacity: 0.9;
}

.log-time {
  color: #909399;
  margin-right: 8px;
}

/* 上传选择卡片 */
.choice-card {
  background: white;
  padding: 32px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s;
  border: 1px solid #ebeef5;
  height: 100%;
}

.choice-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.1);
  border-color: #409eff;
}

.local-upload:hover .icon-wrapper {
  background: #ecf5ff;
  color: #409eff;
}

.pacs-select:hover .icon-wrapper {
  background: #f0f9eb;
  color: #67c23a;
}

.icon-wrapper {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  background: #f2f6fc;
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0 auto 16px;
  font-size: 32px;
  color: #909399;
  transition: all 0.3s;
}

.choice-card h3 {
  margin: 0 0 8px;
  font-size: 18px;
  color: #303133;
}

.choice-card p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}

.choice-card .sub-tip {
  margin-top: 4px;
  color: #909399;
  font-size: 12px;
}

.upload-footer {
  margin-top: 40px;
  color: #909399;
  font-size: 13px;
}

/* 结果展示样式 */
.info-section {
  margin-bottom: 24px;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-card .el-card__body {
  padding: 0;
}

.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 30px;
}

.score-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
}

.score-label {
  font-size: 12px;
  color: #909399;
}

.score-summary {
  width: 100%;
  margin-top: 24px;
  border-top: 1px solid #ebeef5;
  padding-top: 16px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-item .value {
  font-weight: bold;
}

.summary-item .value.danger {
  color: #f56c6c;
}

.summary-result {
  margin-top: 12px;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

/* 质控列表样式 */
.section-title {
  margin-bottom: 16px;
}

.section-title h3 {
  display: inline-flex;
  align-items: center;
  margin: 0;
  font-size: 18px;
  gap: 8px;
}

.subtitle {
  margin-left: 12px;
  font-size: 13px;
  color: #909399;
}

.qc-group {
  margin-bottom: 24px;
}

.group-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding-left: 8px;
  border-left: 4px solid #409eff;
}

.group-title {
  font-size: 16px;
  font-weight: bold;
  margin-right: 12px;
  color: #303133;
}

.qc-list-item {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: all 0.2s;
  cursor: pointer;
}

.qc-list-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  transform: translateX(4px);
}

.qc-list-item.is-error {
  border-left: 4px solid #f56c6c;
}

.qc-list-item.is-success {
  border-left: 4px solid #67c23a;
}

.list-item-left {
  margin-right: 16px;
  padding-top: 4px;
}

.status-icon {
  font-size: 24px;
}

.is-success .status-icon {
  color: #67c23a;
}

.is-error .status-icon {
  color: #f56c6c;
}

.list-item-main {
  flex: 1;
}

.item-header {
  display: flex;
  align-items: center;
  margin-bottom: 6px;
}

.item-name {
  font-size: 16px;
  font-weight: bold;
  margin-right: 12px;
  color: #303133;
}

.item-desc {
  font-size: 14px;
  color: #606266;
  margin-bottom: 6px;
}

.item-detail-text {
  font-size: 13px;
  color: #f56c6c;
  background: #fef0f0;
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.list-item-right {
  display: flex;
  align-items: center;
  margin-left: 16px;
  align-self: center;
}

.mock-image-placeholder {
  margin-top: 20px;
  border: 1px dashed #dcdfe6;
  border-radius: 8px;
  padding: 20px;
  background: #fafafa;
}

/* 动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
