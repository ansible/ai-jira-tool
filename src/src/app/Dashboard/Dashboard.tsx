import * as React from 'react';
import { PageSection, Title, FileUpload, Button, Spinner } from '@patternfly/react-core';
import { Table, Thead, Tr, Th, Tbody, Td } from '@patternfly/react-table';
import {JiraToolAPI} from "../../api";

const Dashboard: React.FunctionComponent = () => {
  const [value, setValue] = React.useState('');
  const [filename, setFilename] = React.useState('');
 // const [files, setFiles] = React.useState([]);
  const [isLoading, setIsLoading] = React.useState(false);
  const [isRejected, setIsRejected] = React.useState(false);
  const [fileLoaded, setFileLoaded] = React.useState(null);

  let promises = [];
  let files = {};

  const handleFileInputChange = (
    _event: React.ChangeEvent<HTMLInputElement> | React.DragEvent<HTMLElement>,
    file: File
  ) => {
    setIsLoading(true);
    setFilename(file.name);
    if(file) {
      const formData = new FormData();
      formData.append('file', file);

      JiraToolAPI.clustering(formData)
        .then((result) => {setIsLoading(false); setValue(result)})
        .catch(() => console.log('reject all files'))
    };
    setIsLoading(false);
  };

  const handleClear = (_event: React.MouseEvent<HTMLButtonElement, MouseEvent>) => {
    setFilename('');
    setValue('');
    setIsRejected(false);
  };
  if (isLoading) {
    return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1" size="lg">AI Jira tool</Title>
      <Spinner/>
    </PageSection>
    )
  };

  return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1" size="lg">AI Jira tool</Title>

      <FileUpload
        id="simple-file"
        value={value}
        filename={filename}
        filenamePlaceholder="Drag and drop a file or upload one"
        onFileInputChange={handleFileInputChange}
        onClearClick={handleClear}
        browseButtonText="Upload"
      />
      {isLoading && <Spinner/>}
      {
        Object.keys(value).length !== 0 &&

        <Table aria-label="Misc table">
          <Thead noWrap>
            <Tr>
              {
                value.column_names.map((name) => <Th>{name}</Th>)
              }
            </Tr>
          </Thead>
          <Tbody>
            {value.data.map((row, rowIndex) => {
              let columns = value.column_names;

              return (
                <Tr
                  key={rowIndex}
                >
                  {
                    columns.map((name) => <Td>
                      {row[name]}
                    </Td>)
                  }
                </Tr>
              );
            })}
          </Tbody>
        </Table> }
    </PageSection>

  )
};

export { Dashboard };
