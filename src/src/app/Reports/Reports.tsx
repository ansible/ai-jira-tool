import * as React from 'react';
import { PageSection, Title, Dropdown, DropdownList, DropdownItem, Button, MenuToggle, MenuToggleElement } from '@patternfly/react-core';
import { Table, Thead, Tr, Th, Tbody, Td } from '@patternfly/react-table';
import {JiraToolAPI} from "../../api";

const Reports: React.FunctionComponent = () => {
  const [state, setState] = React.useState({files: {}, isLoading: true, isOpen: false, selectedFile: {}, selectedFileName: ''});
  function onOpenChange() {
    setState({ ...state, isOpen: !state.isOpen});
  };

  function onToggle() {
    setState({ ...state, isOpen: !state.isOpen});
  };

  function onClick(ev, file) {
    ev.preventDefault();
    setState({ ...state, selectedFile: state.files[file], isOpen: false, selectedFileName: file});
  };

  React.useEffect(() => {
    JiraToolAPI.getAllFiles()
      .then((result) => {setState({...state, files: result.data.files, isLoading: false})})
      .catch(() => console.log('reject all files'));
  }, []);

  if (state.isLoading) {
    return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1" size="lg">AI Jira tool</Title>
    </PageSection>
    )
  };

  return (
    <PageSection hasBodyWrapper={false}>
      <Title headingLevel="h1" size="lg">AI Jira tool</Title>
        <Dropdown
        isOpen={state.isOpen}
        onSelect={() => {}}
        onOpenChange={onOpenChange}
        toggle={(toggleRef: React.Ref<MenuToggleElement>) => (
        <MenuToggle ref={toggleRef} onClick={onToggle} isExpanded={state.isOpen}>
          { Object.keys(state.selectedFile).length !== 0 ? state.selectedFileName : "Dropdown"
           }
        </MenuToggle>
        )}
        ouiaId="BasicDropdown"
        shouldFocusToggleOnSelect
        >
        <DropdownList>
          {
            Object.keys(state.files).map((file) => <DropdownItem
            value={1}
            key="link"
            to="#default-link2"
            onClick={(ev: any) => onClick(ev, file)}
          >
              {file}
          </DropdownItem>)
          }
        </DropdownList>
        </Dropdown>
      {
        Object.keys(state.selectedFile).length !== 0 &&

        <Table aria-label="Misc table">
          <Thead noWrap>
            <Tr>
              {
                state.selectedFile.column_names.map((name) => <Th>{name}</Th>)
              }
            </Tr>
          </Thead>
          <Tbody>
            {state.selectedFile.data.map((row, rowIndex) => {
              let columns = state.selectedFile.column_names;

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
        </Table>
      }
    </PageSection>

  )
};

export { Reports };
