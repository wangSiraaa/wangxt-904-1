import { useState, useEffect } from 'react'
import {
  Table, Button, Space, Tag, Tabs, Card, Row, Col, Empty,
  Timeline, Select, DatePicker, message, Modal, Descriptions, Alert
} from 'antd'
import {
  CheckCircleOutlined, CloseCircleOutlined, WarningOutlined,
  HistoryOutlined, InfoCircleOutlined
} from '@ant-design/icons'
import { duplicateCheckApi, shiftApi, studyRoomApi, volunteerApi } from '../api'
import dayjs from 'dayjs'

const { RangePicker } = DatePicker

function DuplicateChecks() {
  const [data, setData] = useState<any[]>([])
  const [timeline, setTimeline] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [activeTab, setActiveTab] = useState('list')
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [typeFilter, setTypeFilter] = useState<string>('')
  const [detailModal, setDetailModal] = useState(false)
  const [selectedCheck, setSelectedCheck] = useState<any>(null)
  const [rooms, setRooms] = useState<any[]>([])
  const [volunteers, setVolunteers] = useState<any[]>([])

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
    loadTimeline()
    loadRooms()
    loadVolunteers()
  }, [])

  const loadRooms = async () => {
    try {
      const res = await studyRoomApi.list()
      setRooms(res.data)
    } catch (error) {
      // ignore
    }
  }

  const loadVolunteers = async () => {
    try {
      const res = await volunteerApi.list()
      setVolunteers(res.data)
    } catch (error) {
      // ignore
    }
  }

  const loadData = async () => {
    setLoading(true)
    try {
      const params: any = {}
      if (statusFilter) params.status = statusFilter
      if (typeFilter) params.check_type = typeFilter
      const res = await duplicateCheckApi.list(params)
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadTimeline = async () => {
    try {
      const res = await duplicateCheckApi.getTimeline({ days: 30 })
      setTimeline(res.data.timeline || [])
    } catch (error) {
      // ignore
    }
  }

  const canViewAll = user && (user.role === 'admin' || user.role === 'operations')

  const getCheckTypeText = (type: string) => {
    const texts: Record<string, string> = {
      shift_duplicate: '班次重复',
      signup_duplicate: '报名重复',
      attendance_duplicate: '签到重复',
      time_conflict: '时间冲突',
      cross_site_conflict: '跨点位冲突',
      training_required: '培训要求',
      study_room_name_duplicate: '点位名称重复',
      study_room_address_duplicate: '点位地址重复',
    }
    return texts[type] || type
  }

  const getCheckTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      shift_duplicate: 'orange',
      signup_duplicate: 'blue',
      attendance_duplicate: 'purple',
      time_conflict: 'red',
      cross_site_conflict: 'gold',
      training_required: 'cyan',
      study_room_name_duplicate: 'magenta',
      study_room_address_duplicate: 'geekblue',
    }
    return colors[type] || 'default'
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      pass: 'green',
      fail: 'red',
      warning: 'orange',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      pass: '通过',
      fail: '未通过',
      warning: '警告',
    }
    return texts[status] || status
  }

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pass':
        return <CheckCircleOutlined style={{ color: '#52c41a' }} />
      case 'fail':
        return <CloseCircleOutlined style={{ color: '#ff4d4f' }} />
      case 'warning':
        return <WarningOutlined style={{ color: '#faad14' }} />
      default:
        return <InfoCircleOutlined />
    }
  }

  const handleViewDetail = async (record: any) => {
    try {
      const res = await duplicateCheckApi.get(record.id)
      setSelectedCheck(res.data)
      setDetailModal(true)
    } catch (error) {
      message.error('加载详情失败')
    }
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '校验类型',
      dataIndex: 'check_type',
      key: 'check_type',
      width: 120,
      render: (type: string) => (
        <Tag color={getCheckTypeColor(type)}>{getCheckTypeText(type)}</Tag>
      ),
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={getStatusColor(status)}>{getStatusText(status)}</Tag>
      ),
    },
    {
      title: '校验原因',
      dataIndex: 'check_reason',
      key: 'check_reason',
      ellipsis: true,
    },
    {
      title: '点位',
      dataIndex: ['study_room', 'name'],
      key: 'study_room',
      width: 120,
      render: (_: any, record: any) => record.study_room?.name || '-',
    },
    {
      title: '班次ID',
      dataIndex: 'shift_id',
      key: 'shift_id',
      width: 80,
      render: (id: number) => id || '-',
    },
    canViewAll && {
      title: '志愿者',
      dataIndex: ['volunteer', 'name'],
      key: 'volunteer',
      width: 100,
      render: (_: any, record: any) => record.volunteer?.name || '-',
    },
    {
      title: '校验时间',
      dataIndex: 'check_time',
      key: 'check_time',
      width: 160,
      render: (t: string) => dayjs(t).format('YYYY-MM-DD HH:mm:ss'),
    },
    {
      title: '操作',
      key: 'action',
      width: 80,
      render: (_: any, record: any) => (
        <Button type="link" size="small" onClick={() => handleViewDetail(record)}>
          详情
        </Button>
      ),
    },
  ].filter(Boolean)

  const stats = {
    total: data.length,
    pass: data.filter(d => d.status === 'pass').length,
    fail: data.filter(d => d.status === 'fail').length,
    warning: data.filter(d => d.status === 'warning').length,
  }

  const timelineItems = timeline.map((item: any) => ({
    color: item.status === 'pass' ? 'green' : item.status === 'fail' ? 'red' : 'orange',
    children: (
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Space>
            {getStatusIcon(item.status)}
            <Tag color={getCheckTypeColor(item.check_type)}>
              {getCheckTypeText(item.check_type)}
            </Tag>
            <strong>{item.check_reason}</strong>
          </Space>
          <span style={{ color: '#999', fontSize: 12 }}>
            {dayjs(item.check_time).format('MM-DD HH:mm')}
          </span>
        </div>
        {item.conflict_details && (
          <Alert
            style={{ marginTop: 8 }}
            message={item.conflict_details}
            type={item.status === 'pass' ? 'success' : item.status === 'warning' ? 'warning' : 'error'}
            showIcon
          />
        )}
        <div style={{ marginTop: 8, fontSize: 12, color: '#999' }}>
          {item.study_room_name && `点位: ${item.study_room_name}`}
          {item.volunteer_name && ` | 志愿者: ${item.volunteer_name}`}
          {item.checker_name && ` | 校验人: ${item.checker_name}`}
        </div>
      </div>
    ),
  }))

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>重复校验记录</h2>
        <Space>
          <Select
            placeholder="状态筛选"
            style={{ width: 120 }}
            allowClear
            value={statusFilter || undefined}
            onChange={(val) => setStatusFilter(val || '')}
          >
            <Select.Option value="pass">通过</Select.Option>
            <Select.Option value="fail">未通过</Select.Option>
            <Select.Option value="warning">警告</Select.Option>
          </Select>
          <Select
            placeholder="类型筛选"
            style={{ width: 140 }}
            allowClear
            value={typeFilter || undefined}
            onChange={(val) => setTypeFilter(val || '')}
          >
            <Select.Option value="shift_duplicate">班次重复</Select.Option>
            <Select.Option value="signup_duplicate">报名重复</Select.Option>
            <Select.Option value="attendance_duplicate">签到重复</Select.Option>
            <Select.Option value="time_conflict">时间冲突</Select.Option>
            <Select.Option value="cross_site_conflict">跨点位冲突</Select.Option>
            <Select.Option value="training_required">培训要求</Select.Option>
            <Select.Option value="study_room_name_duplicate">点位名称重复</Select.Option>
            <Select.Option value="study_room_address_duplicate">点位地址重复</Select.Option>
          </Select>
          <Button onClick={loadData}>刷新</Button>
        </Space>
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={12} sm={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>总校验数</div>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>{stats.total}</div>
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>通过</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#52c41a' }}>{stats.pass}</div>
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>未通过</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#ff4d4f' }}>{stats.fail}</div>
          </Card>
        </Col>
        <Col xs={12} sm={6}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>警告</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>{stats.warning}</div>
          </Card>
        </Col>
      </Row>

      <Tabs
        activeKey={activeTab}
        onChange={setActiveTab}
        items={[
          {
            key: 'list',
            label: '列表视图',
            children: (
              <Table
                rowKey="id"
                columns={columns}
                dataSource={data}
                loading={loading}
                pagination={{ pageSize: 10 }}
              />
            ),
          },
          {
            key: 'timeline',
            label: '时间线视图',
            children: (
              <Card>
                {timeline.length > 0 ? (
                  <Timeline items={timelineItems} />
                ) : (
                  <Empty description="暂无校验记录" />
                )}
              </Card>
            ),
          },
        ]}
      />

      <Modal
        title="校验详情"
        open={detailModal}
        onCancel={() => setDetailModal(false)}
        footer={[
          <Button key="close" onClick={() => setDetailModal(false)}>
            关闭
          </Button>,
        ]}
        width={600}
      >
        {selectedCheck && (
          <Descriptions column={1} bordered size="small">
            <Descriptions.Item label="校验ID">{selectedCheck.id}</Descriptions.Item>
            <Descriptions.Item label="校验类型">
              <Tag color={getCheckTypeColor(selectedCheck.check_type)}>
                {getCheckTypeText(selectedCheck.check_type)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="状态">
              <Tag color={getStatusColor(selectedCheck.status)}>
                {getStatusText(selectedCheck.status)}
              </Tag>
            </Descriptions.Item>
            <Descriptions.Item label="校验原因">{selectedCheck.check_reason}</Descriptions.Item>
            {selectedCheck.conflict_details && (
              <Descriptions.Item label="冲突详情">
                <Alert
                  message={selectedCheck.conflict_details}
                  type={selectedCheck.status === 'pass' ? 'success' : selectedCheck.status === 'warning' ? 'warning' : 'error'}
                  showIcon
                />
              </Descriptions.Item>
            )}
            {selectedCheck.study_room && (
              <Descriptions.Item label="点位">{selectedCheck.study_room.name}</Descriptions.Item>
            )}
            {selectedCheck.shift_id && (
              <Descriptions.Item label="班次ID">{selectedCheck.shift_id}</Descriptions.Item>
            )}
            {selectedCheck.volunteer && (
              <Descriptions.Item label="志愿者">{selectedCheck.volunteer.name}</Descriptions.Item>
            )}
            {selectedCheck.conflict_entity_id && (
              <Descriptions.Item label="冲突实体ID">{selectedCheck.conflict_entity_id}</Descriptions.Item>
            )}
            {selectedCheck.checker && (
              <Descriptions.Item label="校验人">{selectedCheck.checker.name}</Descriptions.Item>
            )}
            <Descriptions.Item label="校验时间">
              {dayjs(selectedCheck.check_time).format('YYYY-MM-DD HH:mm:ss')}
            </Descriptions.Item>
          </Descriptions>
        )}
      </Modal>
    </div>
  )
}

export default DuplicateChecks
