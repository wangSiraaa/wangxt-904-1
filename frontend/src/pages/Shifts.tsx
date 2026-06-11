import { useState, useEffect } from 'react'
import {
  Table, Button, Modal, Form, Input, InputNumber, Select, DatePicker, TimePicker,
  Space, message, Popconfirm, Tag, Row, Col, Card, Alert
} from 'antd'
import {
  PlusOutlined, EditOutlined, DeleteOutlined,
  PlayCircleOutlined, StopOutlined, ExclamationCircleOutlined
} from '@ant-design/icons'
import { shiftApi, studyRoomApi, signupApi } from '../api'
import dayjs from 'dayjs'

function Shifts() {
  const [data, setData] = useState<any[]>([])
  const [rooms, setRooms] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [user, setUser] = useState<any>(null)
  const [conflictInfo, setConflictInfo] = useState<any>(null)

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
    loadRooms()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await shiftApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const loadRooms = async () => {
    try {
      const res = await studyRoomApi.list()
      setRooms(res.data)
    } catch (error) {
      // ignore
    }
  }

  const canEdit = user && (user.role === 'admin' || user.role === 'operations')
  const isVolunteer = user?.role === 'volunteer'

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue({
      ...record,
      shift_date: dayjs(record.shift_date),
      start_time: dayjs(record.start_time, 'HH:mm:ss'),
      end_time: dayjs(record.end_time, 'HH:mm:ss'),
    })
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await shiftApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handlePublish = async (id: number) => {
    try {
      await shiftApi.publish(id)
      message.success('发布成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '发布失败')
    }
  }

  const handleCancel = async (id: number) => {
    try {
      await shiftApi.cancel(id)
      message.success('已取消班次')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '取消失败')
    }
  }

  const handleSignup = async (shiftId: number) => {
    try {
      const conflictRes = await signupApi.checkConflict(shiftId)
      if (conflictRes.data.has_conflict) {
        setConflictInfo(conflictRes.data)
        Modal.confirm({
          title: '报名冲突提示',
          icon: <ExclamationCircleOutlined style={{ color: '#faad14' }} />,
          content: (
            <div>
              {conflictRes.data.conflicts.map((c: any, i: number) => (
                <Alert
                  key={i}
                  message={c.message}
                  type="warning"
                  showIcon
                  style={{ marginBottom: 8 }}
                />
              ))}
              <p style={{ marginTop: 12 }}>您确定还要报名吗？</p>
            </div>
          ),
          okText: '继续报名',
          cancelText: '取消',
          onOk: async () => {
            try {
              await signupApi.create({ shift_id: shiftId })
              message.success('报名成功')
              loadData()
            } catch (e: any) {
              message.error(e.response?.data?.detail || '报名失败')
            }
          }
        })
        return
      }

      await signupApi.create({ shift_id: shiftId })
      message.success('报名成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '报名失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()
      const submitData = {
        ...values,
        shift_date: values.shift_date.format('YYYY-MM-DD'),
        start_time: values.start_time.format('HH:mm:ss'),
        end_time: values.end_time.format('HH:mm:ss'),
      }

      if (editingId) {
        await shiftApi.update(editingId, submitData)
        message.success('更新成功')
      } else {
        await shiftApi.create(submitData)
        message.success('创建成功')
      }
      setModalVisible(false)
      loadData()
    } catch (error) {
      // 校验错误
    }
  }

  const getStatusColor = (status: string) => {
    const colors: Record<string, string> = {
      draft: 'default',
      published: 'blue',
      full: 'orange',
      completed: 'green',
      cancelled: 'default',
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status: string) => {
    const texts: Record<string, string> = {
      draft: '草稿',
      published: '已发布',
      full: '已满员',
      completed: '已完成',
      cancelled: '已取消',
    }
    return texts[status] || status
  }

  const getShiftTypeColor = (type: string) => {
    const colors: Record<string, string> = {
      morning: 'gold',
      afternoon: 'cyan',
      night: 'purple',
    }
    return colors[type] || 'default'
  }

  const getShiftTypeText = (type: string) => {
    const texts: Record<string, string> = {
      morning: '早班',
      afternoon: '午班',
      night: '晚班',
    }
    return texts[type] || type
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    {
      title: '书房',
      dataIndex: ['study_room', 'name'],
      key: 'study_room',
      render: (_: any, record: any) => record.study_room?.name || '-',
    },
    {
      title: '日期',
      dataIndex: 'shift_date',
      key: 'shift_date',
      width: 120,
      render: (d: string) => dayjs(d).format('YYYY-MM-DD'),
    },
    {
      title: '时段',
      key: 'time',
      width: 150,
      render: (_: any, record: any) => (
        <span>
          {record.start_time?.slice(0, 5)} - {record.end_time?.slice(0, 5)}
        </span>
      ),
    },
    {
      title: '班次类型',
      dataIndex: 'shift_type',
      key: 'shift_type',
      width: 80,
      render: (type: string) => (
        <Tag color={getShiftTypeColor(type)}>{getShiftTypeText(type)}</Tag>
      ),
    },
    {
      title: '人数',
      key: 'count',
      width: 100,
      render: (_: any, record: any) => (
        <span>
          {record.current_volunteers}/{record.max_volunteers}
          {record.current_volunteers >= record.max_volunteers && (
            <Tag color="orange" style={{ marginLeft: 4 }}>满</Tag>
          )}
        </span>
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
  ]

  if (canEdit || isVolunteer) {
    columns.push({
      title: '操作',
      key: 'action',
      width: 200,
      render: (_: any, record: any) => (
        <Space size="small">
          {isVolunteer && record.status === 'published' && record.current_volunteers < record.max_volunteers && (
            <Button type="primary" size="small" onClick={() => handleSignup(record.id)}>
              报名
            </Button>
          )}
          {isVolunteer && record.status === 'full' && (
            <Tag color="orange">已满员</Tag>
          )}
          {canEdit && record.status === 'draft' && (
            <Button type="link" icon={<PlayCircleOutlined />} onClick={() => handlePublish(record.id)}>
              发布
            </Button>
          )}
          {canEdit && (record.status === 'published' || record.status === 'full') && (
            <Button type="link" danger icon={<StopOutlined />} onClick={() => handleCancel(record.id)}>
              取消
            </Button>
          )}
          {canEdit && record.status === 'draft' && (
            <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
              编辑
            </Button>
          )}
          {canEdit && record.status === 'draft' && (
            <Popconfirm title="确定要删除吗？" onConfirm={() => handleDelete(record.id)}>
              <Button type="link" danger icon={<DeleteOutlined />}>
                删除
              </Button>
            </Popconfirm>
          )}
        </Space>
      ),
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>班次管理</h2>
        {canEdit && (
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增班次
          </Button>
        )}
      </div>

      <Row gutter={[16, 16]} style={{ marginBottom: 16 }}>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>总班次</div>
            <div style={{ fontSize: 24, fontWeight: 'bold' }}>{data.length}</div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>已发布</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#1890ff' }}>
              {data.filter(s => s.status === 'published').length}
            </div>
          </Card>
        </Col>
        <Col xs={24} sm={8}>
          <Card size="small">
            <div style={{ fontSize: 12, color: '#999' }}>已满员</div>
            <div style={{ fontSize: 24, fontWeight: 'bold', color: '#faad14' }}>
              {data.filter(s => s.status === 'full').length}
            </div>
          </Card>
        </Col>
      </Row>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title={editingId ? '编辑班次' : '新增班次'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="study_room_id" label="书房点位" rules={[{ required: true, message: '请选择书房' }]}>
            <Select placeholder="请选择书房">
              {rooms.map(room => (
                <Select.Option key={room.id} value={room.id}>{room.name}</Select.Option>
              ))}
            </Select>
          </Form.Item>
          <Form.Item name="shift_date" label="班次日期" rules={[{ required: true, message: '请选择日期' }]}>
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Row gutter={16}>
            <Col span={12}>
              <Form.Item name="start_time" label="开始时间" rules={[{ required: true, message: '请选择开始时间' }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
            <Col span={12}>
              <Form.Item name="end_time" label="结束时间" rules={[{ required: true, message: '请选择结束时间' }]}>
                <TimePicker format="HH:mm" style={{ width: '100%' }} />
              </Form.Item>
            </Col>
          </Row>
          <Form.Item name="shift_type" label="班次类型" rules={[{ required: true, message: '请选择班次类型' }]}>
            <Select placeholder="请选择班次类型">
              <Select.Option value="morning">早班</Select.Option>
              <Select.Option value="afternoon">午班</Select.Option>
              <Select.Option value="night">晚班</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="max_volunteers" label="最大志愿者数" initialValue={3} rules={[{ required: true, message: '请输入人数' }]}>
            <InputNumber min={1} style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="notes" label="备注">
            <Input.TextArea rows={2} placeholder="请输入备注" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Shifts
