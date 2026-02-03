<template>
  <div class="chest-contrast-qc-container">
    <!-- 顶部导航与操作栏 -->
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

    <!-- 1. 上传区域 (当没有数据时显示) -->
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

    <!-- 2. 结果展示区域 (当有数据时显示) -->
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

    <!-- 质控项详情 (分组列表模式) -->
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

// 提交上传并开始分析
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

// 模拟 PACS 选择
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

// 分组计算属性
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

// 添加日志辅助函数
const addLog = (msg) => {
  const time = new Date().toLocaleTimeString('zh-CN', { hour12: false })
  analysisLogs.value.unshift({ time, message: msg })
  // 保持日志最多 5 条
  if (analysisLogs.value.length > 5) analysisLogs.value.pop()
}

// 开始分析流程
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

// 模拟后端 API 请求
const fetchQCData = async () => {
  analyzing.value = true
  // 模拟网络延迟
  await new Promise((resolve) => setTimeout(resolve, 300))

  // 模拟返回数据 - CT胸部增强 (16项)
  qcItems.value = [
    // --- 定位片 (Scout) ---
    {
      name: '扫描范围覆盖',
      phase: '定位片',
      description: '定位片应覆盖肺尖至肺底，包含两侧肋膈角',
      status: '合格',
      detail: '范围完整',
    },
    {
      name: '患者体位',
      phase: '定位片',
      description: '患者身体应居中，无明显倾斜',
      status: '合格',
      detail: '体位正中',
    },

    // --- 平扫期 (Plain) ---
    {
      name: '呼吸运动伪影',
      phase: '平扫期',
      description: '肺纹理清晰，无双影或模糊',
      status: '合格',
      detail: '呼吸配合良好',
    },
    {
      name: '金属伪影',
      phase: '平扫期',
      description: '无体外金属异物干扰',
      status: '不合格',
      detail: '左上肺可见纽扣引起的放射状伪影',
    },
    {
      name: 'FOV设置',
      phase: '平扫期',
      description: '视野范围适中，无截断',
      status: '合格',
      detail: 'FOV 350mm',
    },
    {
      name: '图像噪声(NI)',
      phase: '平扫期',
      description: '噪声指数符合低剂量筛查标准',
      status: '合格',
      detail: 'SD 12.5',
    },

    // --- 增强I期 (Arterial / Enh I) ---
    {
      name: '主动脉强化CT值',
      phase: '增强I期',
      description: '升主动脉CT值应 > 250 HU',
      status: '合格',
      detail: '平均 CT 值 320 HU',
    },
    {
      name: '肺动脉强化',
      phase: '增强I期',
      description: '肺动脉干充盈良好',
      status: '合格',
      detail: '充盈佳',
    },
    {
      name: '对比剂伪影',
      phase: '增强I期',
      description: '上腔静脉无明显硬化伪影',
      status: '合格',
      detail: '轻微硬化，不影响诊断',
    },
    {
      name: '扫描时机',
      phase: '增强I期',
      description: '触发时机准确，无过早或过晚',
      status: '合格',
      detail: 'Bolus Tracking 触发准确',
    },
    {
      name: '外渗检测',
      phase: '增强I期',
      description: '注射部位软组织无肿胀',
      status: '合格',
      detail: '无外渗',
    },

    // --- 增强II期 (Venous / Enh II) ---
    {
      name: '肝门静脉强化',
      phase: '增强II期',
      description: '门静脉系统充盈良好',
      status: '合格',
      detail: '门脉主干 CT 值 140 HU',
    },
    {
      name: '实质脏器强化',
      phase: '增强II期',
      description: '肝脏、脾脏实质强化均匀',
      status: '合格',
      detail: '强化均匀',
    },
    {
      name: '静脉污染',
      phase: '增强II期',
      description: '无明显的造影剂反流',
      status: '合格',
      detail: '无反流',
    },
    {
      name: '图像层厚',
      phase: '增强II期',
      description: '重建层厚应 <= 1.5mm',
      status: '合格',
      detail: '1.0mm',
    },
    {
      name: '整体图像质量',
      phase: '增强II期',
      description: '综合评估信噪比与对比度',
      status: '合格',
      detail: '优',
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
/* 容器与整体布局 */
.chest-contrast-qc-container {
  padding: 24px;
  background-color: #f5f7fa;
  min-height: calc(100vh - 84px); /* 减去顶部导航栏高度 */
}

/* 页面头部 */
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  margin-bottom: 24px;
}

.header-left .el-breadcrumb {
  margin-bottom: 12px;
}

.page-title {
  margin: 0;
  font-size: 24px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-tag {
  font-weight: normal;
}

/* 1. 上传区域样式 */
.upload-section {
  display: flex;
  flex-direction: column;
  /* 固定高度，确保所有页面一致 */
  height: calc(100vh - 180px);
  min-height: 600px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.upload-wrapper {
  width: 100%;
  height: 100%;
  padding: 40px;
  display: flex;
  flex-direction: column;
}

.analyzing-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.upload-choices {
  flex: 1;
  display: flex;
  flex-direction: column;
  /* 内容垂直居中 */
  justify-content: center;
}

/* 卡片行容器 */
.upload-choices .el-row {
  flex: 1; /* 占据中间空间 */
  display: flex;
  align-items: center; /* 垂直居中 */
  width: 100%;
  max-width: 900px;
  margin: 0 auto !important;
}

.upload-footer {
  margin-top: auto; /* 推到底部 */
  padding-top: 20px;
  border-top: 1px solid #eee;
  color: #909399;
  font-size: 13px;
  text-align: center;
}

/* 卡片选择样式 */
.choice-card {
  background: #f8f9fb;
  border: 2px solid #e4e7ed;
  border-radius: 12px;
  padding: 32px 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  height: 220px; /* 固定卡片高度 */
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.choice-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  border-color: #409eff;
}

.icon-wrapper {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 36px;
  transition: all 0.3s;
}

.local-upload .icon-wrapper {
  background: #ecf5ff;
  color: #409eff;
}

.pacs-select .icon-wrapper {
  background: #f0f9eb;
  color: #67c23a;
}

.choice-card:hover .icon-wrapper {
  transform: scale(1.1);
}

.choice-card h3 {
  margin: 0 0 10px;
  font-size: 18px;
  color: #303133;
}

.choice-card p {
  margin: 0 0 5px;
  color: #606266;
  font-size: 14px;
}

.choice-card .sub-tip {
  color: #909399;
  font-size: 12px;
}

.upload-footer p {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
}

/* 分析动画样式 */
.analyzing-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 20px;
}

.scan-animation-box {
  width: 120px;
  height: 120px;
  border: 4px solid #409eff;
  border-radius: 50%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30px;
  overflow: hidden;
  box-shadow: 0 0 15px rgba(64, 158, 255, 0.4);
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
  background: #67c23a;
  box-shadow: 0 0 10px #67c23a;
  animation: scanMove 1.5s linear infinite;
  z-index: 1;
}

@keyframes scanMove {
  0% {
    top: 0;
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  90% {
    opacity: 1;
  }
  100% {
    top: 100%;
    opacity: 0;
  }
}

.progress-info {
  width: 100%;
  max-width: 500px;
  text-align: center;
}

.analyzing-title {
  font-size: 20px;
  color: #303133;
  margin-bottom: 20px;
}

.step-display {
  margin-top: 15px;
  font-size: 14px;
  color: #409eff;
  font-weight: 500;
}

.log-window {
  margin-top: 20px;
  height: 120px;
  background: #2b2b2b;
  border-radius: 4px;
  padding: 10px 15px;
  text-align: left;
  overflow-y: hidden;
  font-family: 'Consolas', monospace;
  font-size: 12px;
  color: #a6a9ad;
}

.log-item {
  margin: 4px 0;
  line-height: 1.4;
  animation: fadeIn 0.3s ease;
}

.log-time {
  color: #67c23a;
  margin-right: 8px;
}

/* 2. 结果展示样式 */
.info-section {
  margin-bottom: 24px;
}

.patient-card,
.score-card {
  height: 100%;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.score-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 10px 0;
}

.score-value {
  display: block;
  font-size: 28px;
  font-weight: bold;
  color: #303133;
}

.score-label {
  display: block;
  font-size: 12px;
  color: #909399;
  margin-top: 4px;
}

.score-summary {
  margin-top: 20px;
  width: 100%;
  padding: 0 20px;
}

.summary-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 14px;
}

.summary-item .label {
  color: #606266;
}

.summary-item .value {
  font-weight: bold;
}

.summary-item .value.danger {
  color: #f56c6c;
}

.summary-result {
  margin-top: 15px;
  padding-top: 15px;
  border-top: 1px dashed #dcdfe6;
  text-align: center;
  font-size: 14px;
  color: #606266;
}

/* 质控项详情样式 */
.section-title {
  margin-bottom: 20px;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.section-title h3 {
  margin: 0;
  font-size: 18px;
  color: #303133;
  display: flex;
  align-items: center;
  gap: 8px;
}

.section-title .subtitle {
  font-size: 13px;
  color: #909399;
}

.qc-list {
  display: flex;
  flex-direction: column;
  gap: 24px; /* 组与组之间的间距 */
}

.qc-group {
  display: flex;
  flex-direction: column;
  gap: 12px; /* 组内列表项间距 */
}

.group-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding-left: 8px;
  border-left: 4px solid #409eff;
  margin-bottom: 8px;
}

.group-title {
  font-size: 16px;
  font-weight: bold;
  color: #303133;
}

.qc-list-item {
  display: flex;
  align-items: center;
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 8px;
  padding: 20px 24px;
  transition: all 0.3s;
  cursor: pointer;
}

.qc-list-item:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  transform: translateY(-2px);
}

.qc-list-item.is-error {
  border-left: 4px solid #f56c6c;
  background: #fff5f5;
}

.qc-list-item.is-success {
  border-left: 4px solid #67c23a;
}

.list-item-left {
  margin-right: 24px;
}

.status-icon {
  font-size: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 50%;
  background: #f2f6fc;
}

.is-success .status-icon {
  color: #67c23a;
  background: #f0f9eb;
}
.is-error .status-icon {
  color: #f56c6c;
  background: #fef0f0;
}

.list-item-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.item-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.item-name {
  font-size: 16px;
  font-weight: 600;
  color: #303133;
}

.item-desc {
  font-size: 14px;
  color: #606266;
  line-height: 1.5;
}

.item-detail-text {
  font-size: 13px;
  color: #f56c6c;
  display: flex;
  align-items: center;
  gap: 6px;
  margin-top: 4px;
  background: rgba(245, 108, 108, 0.1);
  padding: 4px 8px;
  border-radius: 4px;
  width: fit-content;
}

.list-item-right {
  margin-left: 20px;
  display: flex;
  align-items: center;
}

/* Dialog 内容 */
.dialog-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.mock-image-placeholder {
  width: 100%;
  height: 300px;
  background: #000;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  overflow: hidden;
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}
</style>
