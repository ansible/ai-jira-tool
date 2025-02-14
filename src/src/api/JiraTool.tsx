import axios from 'axios';

export class BaseAPI {
  http: { delete; get; interceptors; patch; post; put };

  constructor() {
    this.http = axios.create({
      adapter: 'fetch',
      withCredentials: false,
    });
  }
}

const base = new BaseAPI();

export const JiraToolAPI = {
  getAllFiles: () => base.http.get(`/api/files`),
  upload: (formData) => base.http.post(`/api/upload`, formData),
  table: () => base.http.get(`/api/table`),
  clustering: (formData) => base.http.post(`/api/clustering`, formData),
}

