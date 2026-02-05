import React, { useState, useEffect } from 'react';
import axios from 'axios';
import './App.css';

function App() {
  const [data, setData] = useState({ periods: [], rows: [] });
  const [loading, setLoading] = useState(true);

  const fetchData = async () => {
    try {
      const response = await axios.get('/api/table/');
      setData(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Ошибка загрузки:', error);
    }
  };

  const initTable = async () => {
    try {
      await axios.post('/api/table/init');
      fetchData();
    } catch (error) {
      console.error('Ошибка инициализации:', error);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  const updateCell = async (rowId, periodId, value) => {
    try {
      const numValue = value === '' ? null : parseFloat(value);
      await axios.put(`/api/table/cells/${rowId}/${periodId}?value=${numValue}`);
      fetchData();
    } catch (error) {
      console.error('Ошибка обновления ячейки:', error);
    }
  };

  const updateRowField = async (rowId, field, value) => {
    try {
      await axios.put(`/api/table/rows/${rowId}?${field}=${encodeURIComponent(value)}`);
      fetchData();
    } catch (error) {
      console.error('Ошибка обновления поля:', error);
    }
  };

  const addRow = async () => {
    try {
      await axios.post('/api/table/rows', {
        entity: 'Новое юрлицо',
        article: 'Новая статья',
        project: 'Новый проект'
      });
      fetchData();
    } catch (error) {
      console.error('Ошибка добавления строки:', error);
    }
  };

  const addChildRow = async (parentId) => {
    try {
      await axios.post('/api/table/rows', {
        parent_id: parentId,
        project: 'Подстрока'
      });
      fetchData();
    } catch (error) {
      console.error('Ошибка добавления подстроки:', error);
    }
  };

  const deleteRow = async (rowId) => {
    try {
      await axios.delete(`/api/table/rows/${rowId}`);
      fetchData();
    } catch (error) {
      console.error('Ошибка удаления строки:', error);
    }
  };

  const addPeriod = async () => {
    try {
      await axios.post('/api/table/periods');
      fetchData();
    } catch (error) {
      console.error('Ошибка добавления периода:', error);
    }
  };

  const deletePeriod = async (periodId) => {
    try {
      await axios.delete(`/api/table/periods/${periodId}`);
      fetchData();
    } catch (error) {
      console.error('Ошибка удаления периода:', error);
    }
  };

  const renderRow = (row) => {
    const indent = row.level * 24;
    
    return (
      <React.Fragment key={row.id}>
        <tr className={`level-${row.level}`}>
          <td className="actions-cell">
            <div className="row-controls">
              <button 
                className="btn-icon btn-add" 
                onClick={() => addChildRow(row.id)}
                title="Добавить подстроку"
              >
                +
              </button>
              <button 
                className="btn-icon btn-delete" 
                onClick={() => deleteRow(row.id)}
                title="Удалить"
              >
                ×
              </button>
            </div>
          </td>
          <td className="fixed-col">
            <input
              type="text"
              value={row.entity}
              onChange={(e) => updateRowField(row.id, 'entity', e.target.value)}
              style={{ paddingLeft: `${indent + 12}px` }}
              placeholder="Юр. лицо"
            />
          </td>
          <td className="fixed-col">
            <input
              type="text"
              value={row.article}
              onChange={(e) => updateRowField(row.id, 'article', e.target.value)}
              placeholder="Статья"
            />
          </td>
          <td className="fixed-col">
            <input
              type="text"
              value={row.project}
              onChange={(e) => updateRowField(row.id, 'project', e.target.value)}
              placeholder="Проект"
            />
          </td>
          {data.periods.map(period => {
            const cell = row.cells.find(c => c.period_id === period.id);
            return (
              <td key={period.id} className="period-cell">
                <input
                  type="number"
                  step="any"
                  value={cell?.value ?? ''}
                  onChange={(e) => updateCell(row.id, period.id, e.target.value)}
                  placeholder="—"
                />
              </td>
            );
          })}
        </tr>
        {row.children && row.children.map(child => renderRow(child))}
      </React.Fragment>
    );
  };

  if (loading) return (
    <div className="loading-screen">
      <div className="spinner"></div>
      <p>Загрузка данных...</p>
    </div>
  );

  return (
    <div className="app">
      <header className="app-header">
        <div className="logo">
          <div className="logo-icon">◆</div>
          <h1>Budget Pro</h1>
        </div>
        <p className="subtitle">Система управления бюджетом</p>
      </header>

      <main className="main-content">
        <div className="toolbar">
          <div className="toolbar-left">
            <button onClick={addRow} className="btn btn-primary">
              <span className="btn-icon-text">+</span> Добавить строку
            </button>
            <button onClick={addPeriod} className="btn btn-primary">
              <span className="btn-icon-text">+</span> Добавить период
            </button>
          </div>
          <button onClick={initTable} className="btn btn-secondary">
            ↻ Инициализировать пример
          </button>
        </div>

        <div className="table-card">
          <div className="table-header">
            <h2>Бюджетная таблица</h2>
            <span className="badge">{data.rows.length} строк</span>
          </div>
          
          <div className="table-wrapper">
            <table className="budget-table">
              <thead>
                <tr>
                  <th className="actions-header"></th>
                  <th className="fixed-header">Юр. лицо</th>
                  <th className="fixed-header">Статья</th>
                  <th className="fixed-header">Проект</th>
                  {data.periods.map(period => (
                    <th key={period.id} className="period-header">
                      {period.name}
                      <span 
                        className="delete-period"
                        onClick={() => deletePeriod(period.id)}
                        title="Удалить период"
                      >
                        ×
                      </span>
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.length === 0 ? (
                  <tr>
                    <td colSpan={4 + data.periods.length} className="empty-state">
                      <div className="empty-content">
                        <div className="empty-icon">📊</div>
                        <p>Таблица пуста</p>
                        <button onClick={initTable} className="btn btn-primary">
                          Создать пример
                        </button>
                      </div>
                    </td>
                  </tr>
                ) : (
                  data.rows.map(row => renderRow(row))
                )}
              </tbody>
            </table>
          </div>
        </div>

        <div className="charts-card">
          <div className="charts-header">
            <h2>Аналитика и графики</h2>
            <span className="badge badge-soon">В разработке</span>
          </div>
          <div className="charts-placeholder">
            <div className="chart-icon-large">📈</div>
            <h3>Визуализация данных</h3>
            <p>Графики будут доступны после интеграции с 1С</p>
            <div className="tech-stack">
              <span className="tech-tag">React</span>
              <span className="tech-tag">FastAPI</span>
              <span className="tech-tag">PostgreSQL</span>
              <span className="tech-tag">1С Ready</span>
            </div>
          </div>
        </div>
      </main>

      <footer className="app-footer">
        <p>Prototype v1.0 • Financial Department • 2025</p>
      </footer>
    </div>
  );
}

export default App;
