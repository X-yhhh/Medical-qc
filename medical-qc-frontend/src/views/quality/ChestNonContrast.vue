<template>
  <!-- 
    @file quality/ChestNonContrast.vue
    @description CT胸部平扫智能质控页面
    功能: 
    1. 提供影像上传 (本地/PACS)
    2. 展示 AI 自动分析过程
    3. 显示质控评分、异常项统计及详细检测结果
    
    对接API:
    - POST /quality/chest-non-contrast/analyze (待接入，当前使用前端模拟数据)
  -->
  <div class="head-qc-container">
    <!-- 顶部导航与操作栏 -->
    <div class="page-header">
      <div class="header-left">
        <el-breadcrumb separator="/">
          <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
          <el-breadcrumb-item>影像质控</el-breadcrumb-item>
          <el-breadcrumb-item>CT胸部平扫</el-breadcrumb-item>
        </el-breadcrumb>
        <h2 class="page-title">
          CT胸部平扫智能质控
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
      功能: 提供本地文件拖拽上传和 PACS 系统调取入口
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
      功能: 展示患者基本信息、质控评分仪表盘及具体的质控项列表
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
              <el-descriptions-item label="扫描部位">Chest Routine</el-descriptions-item>
              <el-descriptions-item label="图像层数"
                >{{ patientInfo.sliceCount }} 层</el-descriptions-item
              >
              <el-descriptions-item label="层厚"
                >{{ patientInfo.sliceThickness }} mm</el-descriptions-item
              >
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
      @section 质控项详情列表
      功能: 展示每一项检测指标的状态（合格/不合格）及详细描述
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
        <div
          v-for="(item, index) in qcItems"
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

    <!-- 详情弹窗 (Mock) -->
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

    <!-- 新建案例弹窗 -->
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

// 打开上传弹窗
const openUploadDialog = (mode = 'local') => {
  uploadMode.value = mode
  uploadForm.patientName = ''
  uploadForm.examId = ''
  selectedFile.value = null
  uploadDialogVisible.value = true
}

// 处理弹窗内的文件选择
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
 * 2. 填充模拟的患者数据
 * 3. 自动打开上传确认弹窗
 */
const simulatePacsSelect = () => {
  ElMessage.success('已连接 PACS 系统，正在检索今日检查列表...')
  // 模拟从 PACS 获取到数据，弹出对话框让用户确认
  setTimeout(() => {
    uploadForm.patientName = '王某某'
    uploadForm.examId = 'PACS_CHEST_20231024'
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
})

// 质控项数据
const qcItems = ref([])

// 重置上传 (改为打开弹窗)
const resetUpload = () => {
  openUploadDialog()
}

// 添加日志辅助函数
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
 * 逻辑:
 * 1. 初始化状态
 * 2. 遍历预定义的分析步骤，更新进度条和日志
 * 3. 模拟数据提取过程中的患者信息填充
 * 4. 流程结束后调用 fetchQCData 获取结果
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
    { progress: 30, msg: '校验序列完整性 (300/300 slices)...', step: '完整性校验' },
    {
      progress: 45,
      msg: `提取患者元数据: ${uploadForm.patientName || '未知'}, ...`,
      step: '元数据提取',
    },
    { progress: 60, msg: 'AI 模型加载中 (Chest_CT_QC_v1.5)...', step: '模型加载' },
    { progress: 80, msg: '正在检测呼吸伪影与心脏运动伪影...', step: '特征提取' },
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
        age: 40 + Math.floor(Math.random() * 40), // 模拟自动获取
        studyId: uploadForm.examId || 'UNKNOWN',
        accessionNumber: 'ACC' + Math.floor(Math.random() * 100000), // 模拟自动获取
        studyDate: new Date().toLocaleString(), // 模拟自动获取
        device: 'GE Revolution CT', // 模拟自动获取
        sliceCount: 300, // 模拟自动获取
        sliceThickness: 1.25, // 模拟自动获取
      }
    }
  }

  await fetchQCData()
}

// 计算异常数量
const abnormalCount = computed(() => {
  return qcItems.value.filter((item) => item.status === '不合格').length
})

// 计算质控分数 (简单逻辑：每个合格项得 100/总数 分，向下取整)
const qualityScore = computed(() => {
  if (qcItems.value.length === 0) return 0
  const passed = qcItems.value.filter((item) => item.status === '合格').length
  return Math.round((passed / qcItems.value.length) * 100)
})

// 分数颜色
const scoreColor = computed(() => {
  if (qualityScore.value >= 90) return '#67C23A'
  if (qualityScore.value >= 60) return '#E6A23C'
  return '#F56C6C'
})

/**
 * @function fetchQCData
 * @description 获取质控检测结果 (Mock)
 * 
 * 对接API:
 * - (计划中) GET /api/quality/chest-non-contrast/result
 * 
 * 当前逻辑:
 * 返回静态模拟数据，包含扫描范围、呼吸伪影、金属伪影等检测项
 */
const fetchQCData = async () => {
  analyzing.value = true
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 300))

  // 模拟返回数据 - CT胸部平扫质控项
  qcItems.value = [
    {
      name: '扫描范围',
      status: '合格',
      description: '肺尖至肺底完整覆盖',
      detail: '',
    },
    {
      name: '呼吸伪影',
      status: '合格',
      description: '无明显呼吸运动伪影',
      detail: '',
    },
    {
      name: '体位不正',
      status: '合格',
      description: '患者居中，无倾斜',
      detail: '',
    },
    {
      name: '金属伪影',
      status: '不合格',
      description: '无明显金属伪影干扰',
      detail: '左侧胸壁可见少量金属伪影',
    },
    {
      name: '图像噪声',
      status: '合格',
      description: '噪声指数符合诊断要求',
      detail: '',
    },
    {
      name: '肺窗设置',
      status: '合格',
      description: '窗宽窗位适宜观察肺纹理',
      detail: '',
    },
    {
      name: '纵隔窗设置',
      status: '合格',
      description: '窗宽窗位适宜观察纵隔结构',
      detail: '',
    },
    {
      name: '心影干扰',
      status: '合格',
      description: '心脏搏动伪影在可接受范围内',
      detail: '',
    },
  ]

  analyzing.value = false
}

// 重新分析
const handleReanalyze = () => {
  ElMessage.info('正在请求云端 AI 重新分析...')
  fetchQCData().then(() => {
    ElMessage.success('分析完成，数据已更新')
  })
}

// 导出报告
const handleExport = () => {
  ElMessage.success('质控报告已生成并开始下载')
}

// 查看详情
const viewDetails = (item) => {
  currentItem.value = item
  dialogVisible.value = true
}
</script>

<style scoped>
/* 
  @section 样式定义
  复用 Head.vue 的样式结构，包含布局、卡片、动画等
*/
.head-qc-container {
  padding: 20px;
}
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.page-title {
  margin-top: 10px;
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 22px;
  color: #303133;
}
.upload-section {
  display: flex;
  justify-content: center;
  margin-top: 40px;
}
.upload-wrapper {
  width: 100%;
  max-width: 900px;
  min-height: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  padding: 40px;
  position: relative;
  overflow: hidden;
}

/* 上传卡片样式 */
.choice-card {
  border: 2px dashed #dcdfe6;
  border-radius: 12px;
  padding: 30px 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.3s;
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}
.choice-card:hover {
  border-color: #409eff;
  background-color: #f0f9eb;
  transform: translateY(-5px);
}
.choice-card .icon-wrapper {
  font-size: 48px;
  margin-bottom: 15px;
  color: #909399;
}
.choice-card:hover .icon-wrapper {
  color: #409eff;
}
.choice-card h3 {
  margin: 0 0 10px;
  font-size: 18px;
  color: #303133;
}
.choice-card p {
  margin: 0;
  color: #606266;
  font-size: 14px;
}
.choice-card .sub-tip {
  font-size: 12px;
  color: #909399;
  margin-top: 5px;
}

.upload-footer {
  margin-top: 40px;
  text-align: center;
  color: #909399;
  font-size: 13px;
}

/* 分析中动画 */
.analyzing-container {
  text-align: center;
  padding: 20px;
}
.scan-animation-box {
  width: 120px;
  height: 120px;
  margin: 0 auto 30px;
  background: #f2f6fc;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  overflow: hidden;
  border: 4px solid #e1f3d8;
}
.scan-icon {
  font-size: 50px;
  color: #67c23a;
}
.scan-line {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 4px;
  background: linear-gradient(to right, transparent, #409eff, transparent);
  animation: scan 2s infinite linear;
}
@keyframes scan {
  0% { top: 0; }
  100% { top: 100%; }
}
.analyzing-title {
  margin-bottom: 20px;
  color: #303133;
}
.step-display {
  margin-top: 10px;
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
}
.log-window {
  margin-top: 20px;
  background: #f4f4f5;
  padding: 10px;
  border-radius: 4px;
  height: 120px;
  overflow: hidden;
  text-align: left;
  font-family: monospace;
  font-size: 12px;
}
.log-item {
  margin: 4px 0;
  color: #606266;
  animation: fadeIn 0.5s;
}
.log-time {
  color: #909399;
  margin-right: 8px;
}

/* 结果展示区 */
.result-section {
  animation: slideUp 0.5s ease-out;
}
.patient-card {
  height: 100%;
}
.score-card {
  height: 100%;
}
.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 10px;
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
  margin-top: 20px;
}
.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 10px;
  font-size: 14px;
}
.summary-result {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px solid #ebeef5;
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-weight: bold;
}
.value.danger {
  color: #f56c6c;
  font-weight: bold;
}

/* 质控列表 */
.qc-items-section {
  margin-top: 24px;
}
.section-title h3 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 5px;
}
.subtitle {
  font-size: 13px;
  color: #909399;
}
.qc-list {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}
.qc-list-item {
  background: white;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 16px;
  display: flex;
  align-items: flex-start;
  gap: 16px;
  cursor: pointer;
  transition: all 0.2s;
}
.qc-list-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}
.qc-list-item.is-error {
  border-left: 4px solid #f56c6c;
}
.qc-list-item.is-success {
  border-left: 4px solid #67c23a;
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
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.item-name {
  font-weight: 600;
  color: #303133;
}
.item-desc {
  font-size: 13px;
  color: #606266;
  margin-bottom: 4px;
}
.error-text {
  color: #f56c6c;
  font-size: 12px;
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 弹窗 */
.dialog-content {
  text-align: left;
}
.mock-image-placeholder {
  margin-top: 20px;
  background: #000;
  display: flex;
  justify-content: center;
  padding: 20px;
  border-radius: 4px;
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
@keyframes slideUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
</style>
