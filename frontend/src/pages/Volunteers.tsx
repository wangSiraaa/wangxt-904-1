import { useState, useEffect } from 'react'
import { Table, Button, Space, message, Tag, Modal, Select, DatePicker, Form, Input } from 'antd'
import { EditOutlined, CheckCircleOutlined, CloseCircleOutlined } from '@ant-design/icons'
import { volunteerApi } from '../api'
import dayjs from 'dayjs'

function Volunteers() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [user, setUser] = useState<any>(null)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()

  useEffect(() => {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      setUser(JSON.parse(userStr))
    }
    loadData()
  }, [])

  const loadData = async () => {
    setLoading(true)
    try {
      const res = await volunteerApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const canEditTraining = user && (user.role === 'training' || user.role === 'admin')

  const handleEditTraining = (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue({
      training_status: record.volunteer_profile?.training_status || 'none',
      training_date: record.volunteer_profile?.training_date
        ? dayjs(record.volunteer_profile.training_date)
        : null,
      training_teacher: record.volunteer_profile?.training_teacher || '',
    })
    setModalVisible(true)
  }

  const handleSubmit = async () => {
    if (!editingId) return
    try {
      const values = await form.validateFields()
      await volunteerApi.updateTraining(editingId, {
        training_status: values.training_status,
        training_date: values.training_date?.format('YYYY-MM-DD'),
        training_teacher: values.training_teacher,
      })
      message.success('培训状态更新成功')
      setModalVisible(false)
      loadData()
    } catch (error) {
      // 校验错误
    }
  }

  const getTrainingColor = (status: string) => {
    const colors: Record<string, string> = {
      none: 'default',
      pending: 'orange',
      completed: 'green',
      failed: 'red',
    }
    return colors[status] || 'default'
  }

  const getTrainingText = (status: string) => {
    const texts: Record<string, string> = {
      none: '未培训',
      pending: '培训中',
      completed: '已完成',
      failed: '未通过',
    }
    return texts[status] || status
  }

  const columns = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '用户名', dataIndex: 'username', key: 'username' },
    { title: '姓名', dataIndex: 'name', key: 'name' },
    {
      title: '培训状态',
      key: 'training',
      width: 100,
      render: (_: any, record: any) => (
        <Tag color={getTrainingColor(record.volunteer_profile?.training_status)}>
          {getTrainingText(record.volunteer_profile?.training_status)}
        </Tag>
      ),
    },
    {
      title: '培训日期',
      key: 'training_date',
      width: 120,
      render: (_: any, record: any) =>
        record.volunteer_profile?.training_date
          ? dayjs(record.volunteer_profile.training_date).format('YYYY-MM-DD')
          : '-',
    },
    {
      title: '培训讲师',
      key: 'training_teacher',
      render: (_: any, record: any) => record.volunteer_profile?.training_teacher || '-',
    },
    { title: '手机', dataIndex: 'phone', key: 'phone' },
    {
      title: '技能',
      key: 'skills',
      render: (_: any, record: any) => record.volunteer_profile?.skills || '-',
    },
  ]

  if (canEditTraining) {
    columns.push({
      title: '操作',
      key: 'action',
      width: 120,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button
            type="link"
            icon={<EditOutlined />}
            onClick={() => handleEditTraining(record)}
          >
            更新培训
          </Button>
        </Space>
      ),
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>志愿者管理</h2>
        <Space>
          <Tag color="green">已完成: {data.filter(v => v.volunteer_profile?.training_status === 'completed').length}</Tag>
          <Tag color="orange">培训中: {data.filter(v => v.volunteer_profile?.training_status === 'pending').length}</Tag>
          <Tag color="default">未培训: {data.filter(v => !v.volunteer_profile || v.volunteer_profile.training_status === 'none').length}</Tag>
        </Space>
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
        pagination={{ pageSize: 10 }}
      />

      <Modal
        title="更新培训状态"
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={500}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="training_status" label="培训状态" rules={[{ required: true, message: '请选择状态' }]}>
            <Select>
              <Select.Option value="none">未培训</Select.Option>
              <Select.Option value="pending">培训中</Select.Option>
              <Select.Option value="completed">已完成</Select.Option>
              <Select.Option value="failed">未通过</Select.Option>
            </Select>
          </Form.Item>
          <Form.Item name="training_date" label="培训日期">
            <DatePicker style={{ width: '100%' }} />
          </Form.Item>
          <Form.Item name="training_teacher" label="培训讲师">
            <Input placeholder="请输入讲师姓名" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default Volunteers
