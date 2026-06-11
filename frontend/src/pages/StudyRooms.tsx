import { useState, useEffect } from 'react'
import { Table, Button, Modal, Form, Input, InputNumber, Select, Space, message, Popconfirm, Tag, Alert } from 'antd'
import { PlusOutlined, EditOutlined, DeleteOutlined, ExclamationCircleOutlined } from '@ant-design/icons'
import { studyRoomApi } from '../api'

function StudyRooms() {
  const [data, setData] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [modalVisible, setModalVisible] = useState(false)
  const [editingId, setEditingId] = useState<number | null>(null)
  const [form] = Form.useForm()
  const [user, setUser] = useState<any>(null)
  const [nameDuplicate, setNameDuplicate] = useState(false)

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
      const res = await studyRoomApi.list()
      setData(res.data)
    } catch (error) {
      message.error('加载失败')
    } finally {
      setLoading(false)
    }
  }

  const handleAdd = () => {
    setEditingId(null)
    form.resetFields()
    setModalVisible(true)
  }

  const handleEdit = (record: any) => {
    setEditingId(record.id)
    form.setFieldsValue(record)
    setModalVisible(true)
  }

  const handleDelete = async (id: number) => {
    try {
      await studyRoomApi.delete(id)
      message.success('删除成功')
      loadData()
    } catch (error: any) {
      message.error(error.response?.data?.detail || '删除失败')
    }
  }

  const handleSubmit = async () => {
    try {
      const values = await form.validateFields()

      const isDuplicate = data.some(room =>
        room.name === values.name && room.id !== editingId
      )
      if (isDuplicate) {
        Modal.error({
          title: '点位名称重复',
          content: (
            <div>
              <Alert
                message="点位名称已存在"
                type="error"
                showIcon
              />
              <p style={{ marginTop: 12 }}>
                原因：名称为“{values.name}”的书房点位已存在，请使用不同的名称。
              </p>
            </div>
          ),
        })
        setNameDuplicate(true)
        return
      }

      const isAddrDuplicate = data.some(room =>
        room.address && values.address && room.address === values.address && room.id !== editingId
      )
      if (isAddrDuplicate) {
        Modal.warning({
          title: '点位地址重复',
          icon: <ExclamationCircleOutlined />,
          content: (
            <div>
              <Alert
                message="相同地址已存在其他点位"
                type="warning"
                showIcon
              />
              <p style={{ marginTop: 12 }}>
                <strong>原因：</strong>地址“{values.address}”已用于其他书房点位。
              </p>
              <p>是否继续创建？</p>
            </div>
          ),
          onOk: async () => {
            try {
              if (editingId) {
                await studyRoomApi.update(editingId, values)
                message.success('更新成功')
              } else {
                await studyRoomApi.create(values)
                message.success('创建成功')
              }
              setModalVisible(false)
              setNameDuplicate(false)
              loadData()
            } catch (e) {
              // ignore
            }
          }
        })
        return
      }

      if (editingId) {
        await studyRoomApi.update(editingId, values)
        message.success('更新成功')
      } else {
        await studyRoomApi.create(values)
        message.success('创建成功')
      }
      setModalVisible(false)
      setNameDuplicate(false)
      loadData()
    } catch (error) {
      // 校验错误不处理
    }
  }

  const canEdit = user && (user.role === 'admin' || user.role === 'operations')

  const columns: any[] = [
    { title: 'ID', dataIndex: 'id', key: 'id', width: 60 },
    { title: '名称', dataIndex: 'name', key: 'name' },
    { title: '地址', dataIndex: 'address', key: 'address' },
    { title: '容量', dataIndex: 'capacity', key: 'capacity', width: 80 },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      width: 80,
      render: (status: string) => (
        <Tag color={status === 'active' ? 'green' : 'default'}>
          {status === 'active' ? '启用' : '停用'}
        </Tag>
      )
    },
    { title: '创建时间', dataIndex: 'created_at', key: 'created_at', width: 180 },
  ]

  if (canEdit) {
    columns.push({
      title: '操作',
      key: 'action',
      width: 150,
      render: (_: any, record: any) => (
        <Space size="small">
          <Button type="link" icon={<EditOutlined />} onClick={() => handleEdit(record)}>
            编辑
          </Button>
          <Popconfirm title="确定要删除吗？" onConfirm={() => handleDelete(record.id)}>
            <Button type="link" danger icon={<DeleteOutlined />}>
              删除
            </Button>
          </Popconfirm>
        </Space>
      )
    })
  }

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 16 }}>
        <h2 style={{ margin: 0 }}>书房点位</h2>
        {canEdit && (
          <Button type="primary" icon={<PlusOutlined />} onClick={handleAdd}>
            新增点位
          </Button>
        )}
      </div>

      <Table
        rowKey="id"
        columns={columns}
        dataSource={data}
        loading={loading}
      />

      <Modal
        title={editingId ? '编辑点位' : '新增点位'}
        open={modalVisible}
        onOk={handleSubmit}
        onCancel={() => setModalVisible(false)}
        width={600}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="名称" rules={[{ required: true, message: '请输入名称' }]}>
            <Input placeholder="请输入书房名称" />
          </Form.Item>
          <Form.Item name="address" label="地址">
            <Input placeholder="请输入地址" />
          </Form.Item>
          <Form.Item name="description" label="描述">
            <Input.TextArea rows={3} placeholder="请输入描述" />
          </Form.Item>
          <Form.Item name="capacity" label="容量" initialValue={30}>
            <InputNumber min={1} style={{ width: '100%' }} placeholder="请输入容量" />
          </Form.Item>
          <Form.Item name="status" label="状态" initialValue="active">
            <Select>
              <Select.Option value="active">启用</Select.Option>
              <Select.Option value="inactive">停用</Select.Option>
            </Select>
          </Form.Item>
        </Form>
      </Modal>
    </div>
  )
}

export default StudyRooms
